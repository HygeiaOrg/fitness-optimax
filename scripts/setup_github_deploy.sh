#!/usr/bin/env bash
# One-off: let GitHub Actions deploy Fitness OptiMax to Cloud Run without a
# stored key (Workload Identity Federation). Run once from a machine where
# `gcloud` is logged in as a project owner and `gh` is logged in to GitHub.
#
#   bash scripts/setup_github_deploy.sh
#
# Safe to re-run: it creates what's missing and re-applies the access rules.
#
# Only workflows running on refs/heads/master of this exact repository (matched
# by its numeric id, so a re-created repo with the same name doesn't qualify)
# can get deployer tokens, and the deployer's roles are scoped as narrowly as
# `gcloud run deploy --source` allows.
set -euo pipefail

PROJECT_ID=gen-lang-client-0937519537
PROJECT_NUMBER=881889452278
REGION=europe-west2
SERVICE=fitness-optimax
REPO=HygeiaOrg/fitness-optimax
REPO_ID=1282794442
SA_NAME=github-deployer
SA="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"
POOL=github
PROVIDER=github
AR_REPO=cloud-run-source-deploy
BUILD_BUCKET="gs://run-sources-${PROJECT_ID}-${REGION}"   # where `gcloud run deploy --source` uploads

g() { gcloud --project "$PROJECT_ID" --quiet "$@"; }

echo "==> Enabling APIs"
g services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
  iamcredentials.googleapis.com sts.googleapis.com bigquery.googleapis.com drive.googleapis.com

echo "==> Deployer service account"
g iam service-accounts describe "$SA" >/dev/null 2>&1 || \
  g iam service-accounts create "$SA_NAME" --display-name="GitHub Actions deployer"

echo "==> Project roles (deploy, build, BigQuery views)"
for role in roles/run.admin roles/cloudbuild.builds.editor roles/serviceusage.serviceUsageConsumer \
            roles/bigquery.dataEditor roles/bigquery.jobUser roles/logging.viewer; do
  g projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$SA" \
    --role="$role" --condition=None >/dev/null
done

echo "==> Act-as only the Cloud Run runtime service account"
RUNTIME_SA=$(g run services describe "$SERVICE" --region "$REGION" \
  --format='value(spec.template.spec.serviceAccountName)' 2>/dev/null || true)
RUNTIME_SA=${RUNTIME_SA:-"$PROJECT_NUMBER-compute@developer.gserviceaccount.com"}
echo "    runtime SA: $RUNTIME_SA"
g iam service-accounts add-iam-policy-binding "$RUNTIME_SA" \
  --member="serviceAccount:$SA" --role=roles/iam.serviceAccountUser >/dev/null

echo "==> Artifact Registry repo for source deploys (writer only)"
g artifacts repositories describe "$AR_REPO" --location="$REGION" >/dev/null 2>&1 || \
  g artifacts repositories create "$AR_REPO" --location="$REGION" --repository-format=docker \
    --description="Cloud Run source deployments"
g artifacts repositories add-iam-policy-binding "$AR_REPO" --location="$REGION" \
  --member="serviceAccount:$SA" --role=roles/artifactregistry.writer >/dev/null

echo "==> Source upload bucket (object access on that bucket only)"
gcloud storage buckets describe "$BUILD_BUCKET" --project "$PROJECT_ID" >/dev/null 2>&1 || \
  gcloud storage buckets create "$BUILD_BUCKET" --project "$PROJECT_ID" --location="$REGION" --uniform-bucket-level-access
for role in roles/storage.objectAdmin roles/storage.legacyBucketReader; do
  gcloud storage buckets add-iam-policy-binding "$BUILD_BUCKET" \
    --member="serviceAccount:$SA" --role="$role" >/dev/null
done

echo "==> Workload Identity pool + GitHub provider (master of $REPO only)"
CONDITION="assertion.repository_id == '$REPO_ID' && assertion.ref == 'refs/heads/master'"
MAPPING="google.subject=assertion.sub,attribute.repository_id=assertion.repository_id,attribute.ref=assertion.ref"
g iam workload-identity-pools describe "$POOL" --location=global >/dev/null 2>&1 || \
  g iam workload-identity-pools create "$POOL" --location=global --display-name="GitHub Actions"
if g iam workload-identity-pools providers describe "$PROVIDER" --location=global \
     --workload-identity-pool="$POOL" >/dev/null 2>&1; then
  g iam workload-identity-pools providers update-oidc "$PROVIDER" --location=global \
    --workload-identity-pool="$POOL" --attribute-mapping="$MAPPING" --attribute-condition="$CONDITION"
else
  g iam workload-identity-pools providers create-oidc "$PROVIDER" --location=global \
    --workload-identity-pool="$POOL" --display-name="GitHub" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-mapping="$MAPPING" --attribute-condition="$CONDITION"
fi

g iam service-accounts add-iam-policy-binding "$SA" \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL/attribute.repository_id/$REPO_ID" \
  >/dev/null

WIF="projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL/providers/$PROVIDER"

echo "==> GitHub repository variables"
gh variable set GCP_WIF_PROVIDER --repo "$REPO" --body "$WIF"
gh variable set GCP_DEPLOY_SA --repo "$REPO" --body "$SA"

echo "==> Protect master: CI must pass before anything merges"
gh api -X PUT "repos/$REPO/branches/master/protection" --input - >/dev/null <<JSON || \
  echo "    (couldn't set branch protection; set it in GitHub → Settings → Branches)"
{
  "required_status_checks": {"strict": true, "contexts": ["API tests + exercise catalogue", "Frontend lint + build"]},
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null
}
JSON

echo
echo "Done. Merges to master now deploy automatically."
echo "One manual step left: share the 'Fitness OptiMax' source Google Sheet with"
echo "  $SA  (Viewer), so CI can redeploy the BigQuery views that read it."
