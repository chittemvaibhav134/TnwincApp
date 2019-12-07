IMPORT_DIR="/import" 
if [[ "${S3_CONFIG_BUCKET}" ]]; then
    echo "Pulling config from $S3_CONFIG_BUCKET to $IMPORT_DIR"
    aws s3 sync s3://$S3_CONFIG_BUCKET $IMPORT_DIR
else
    echo "S3_CONFIG_BUCKET env variable not found; skipping external config pull"
fi