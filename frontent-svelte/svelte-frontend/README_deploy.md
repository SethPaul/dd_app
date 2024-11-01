# Login to ECR
export ACCOUNT_ID=<your account id>
export REGION=<your region>

aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Build the image
docker build -t svelte-app .

# Tag the image
docker tag svelte-app:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/svelte-app:latest

# Push the image
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/svelte-app:latest

