# CI/CD Pipeline Setup

## GitHub Actions Workflows

### 1. Test Workflow (`.github/workflows/test.yml`)
- **Triggers:** Push to main/develop, PRs
- **What it does:**
  - Sets up Python 3.10
  - Installs dependencies
  - Runs tests (if you have any)
  - Builds Docker image to verify it works

### 2. Docker Build Workflow (`.github/workflows/docker.yml`)
- **Triggers:** Push to main/develop, PRs
- **What it does:**
  - Builds Docker image
  - Pushes to Docker Hub
  - Uses layer caching for speed

### 3. Deploy Workflow (`.github/workflows/deploy.yml`)
- **Triggers:** Push to main only
- **What it does:**
  - SSH into your server
  - Pulls latest Docker image
  - Restarts containers

## Setup Instructions

### For Test Workflow
No setup needed - works out of the box!

### For Docker Build Workflow

1. **Create Docker Hub account:** https://hub.docker.com/

2. **Add GitHub Secrets:**
   - Go to: Repository → Settings → Secrets and variables → Actions
   - Add:
     - `DOCKER_USERNAME`: Your Docker Hub username
     - `DOCKER_PASSWORD`: Your Docker Hub password or access token

3. **Update workflow file:**
   - Replace `DOCKER_USERNAME` in the workflow with your actual username
   - Or use `${{ secrets.DOCKER_USERNAME }}` in the tags section

### For Deploy Workflow

1. **Prepare your server:**
   - Install Docker and docker-compose
   - Set up SSH access

2. **Add GitHub Secrets:**
   - `SERVER_HOST`: Your server IP/domain
   - `SERVER_USER`: SSH username
   - `SSH_KEY`: Private SSH key content

3. **Update deploy script:**
   - Change `/path/to/app` to your actual app directory

## Usage

### Local Testing Before CI/CD
```bash
# Test build locally
docker build -t construction-planner .

# Test docker-compose
docker-compose up --build
```

### Trigger Workflows
- **Test:** Push any branch or create PR
- **Build:** Push to main/develop
- **Deploy:** Push to main

### Manual Trigger
- Go to Actions tab in GitHub
- Select workflow
- Click "Run workflow"

## Alternative: GitLab CI

If using GitLab, create `.gitlab-ci.yml`:

```yaml
stages:
  - build
  - test
  - deploy

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t construction-planner .

test:
  stage: test
  image: python:3.10
  script:
    - pip install -r requirements.txt
    - python -m pytest backend/

deploy:
  stage: deploy
  image: docker:latest
  script:
    - docker-compose up -d
  only:
    - main
```

## Tips

1. **Start simple:** Begin with just the test workflow
2. **Add Docker Hub:** Once tests pass, add Docker build
3. **Add deployment:** Last step after everything works
4. **Use branches:** Use `develop` for testing, `main` for production
5. **Monitor logs:** Check Actions tab for workflow logs
