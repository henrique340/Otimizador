pipeline {
  agent any

  stages {
    stage('Install') {
      steps {
        sh 'python3 -m pip install --upgrade pip'
        sh 'python3 -m pip install -r requirements.txt -r requirements-dev.txt'
      }
    }

    stage('Lint') {
      steps {
        sh 'python3 -m ruff check src tests'
      }
    }

    stage('Test') {
      steps {
        sh 'python3 -m pytest -q'
      }
    }

    stage('Package') {
      steps {
        sh 'bash scripts/package_lambda.sh'
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'dist/*.zip', fingerprint: true, allowEmptyArchive: true
    }
  }
}
