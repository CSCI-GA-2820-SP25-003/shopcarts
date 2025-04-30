# NYU DevOps Project Template

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Language-Python-blue.svg)](https://python.org/)
[![codecov](https://codecov.io/gh/CSCI-GA-2820-SP25-003/shopcarts/graph/badge.svg?token=F7RHYXIWMA)](https://codecov.io/gh/CSCI-GA-2820-SP25-003/shopcarts)
[![Build Status](https://github.com/CSCI-GA-2820-SP25-003/shopcarts/actions/workflows/ci.yml/badge.svg)](https://github.com/CSCI-GA-2820-SP25-003/shopcarts/actions)

## Overview

The `/service` folder contains `models.py` file for the model and a `routes.py` file for the service. The `/tests` folder has test cases for testing the model and the service separately. You can use the [lab-flask-tdd](https://github.com/nyu-devops/lab-flask-tdd) for code examples to copy from.

## Automatic Setup

The best way to use this repo is to start your own repo using it as a git template. To do this just press the green **Use this template** button in GitHub and this will become the source for your repository.

## Manual Setup

You can also clone this repository and then copy and paste the starter code into your project repo folder on your local computer. Be careful not to copy over your own `README.md` file so be selective in what you copy.

There are 4 hidden files that you will need to copy manually if you use the Mac Finder or Windows Explorer to copy files from this folder into your repo folder.

These should be copied using a bash shell as follows:

```bash
    cp .gitignore  ../<your_repo_folder>/
    cp .flaskenv ../<your_repo_folder>/
    cp .gitattributes ../<your_repo_folder>/
```

## Contents

The project contains the following:

```text
.gitignore          - this will ignore vagrant and other metadata files
.flaskenv           - Environment variables to configure Flask
.gitattributes      - File to gix Windows CRLF issues
.devcontainers/     - Folder with support for VSCode Remote Containers
dot-env-example     - copy to .env to use environment variables
pyproject.toml      - Poetry list of Python libraries required by your code

service/                   - service python package
├── __init__.py            - package initializer
├── config.py              - configuration parameters
├── models.py              - module with business models
├── routes.py              - module with service routes
└── common                 - common code package
    ├── cli_commands.py    - Flask command to recreate all tables
    ├── error_handlers.py  - HTTP error handling code
    ├── log_handlers.py    - logging setup code
    └── status.py          - HTTP status constants

tests/                     - test cases package
├── __init__.py            - package initializer
├── factories.py           - Factory for testing with fake objects
├── test_cli_commands.py   - test suite for the CLI
├── test_models.py         - test suite for business models
└── test_routes.py         - test suite for service routes
```

## Shopcart Model Overview

This service provides an API for managing shopping carts. Developers can easily set up and run the project using **DevContainer** in **VS Code** with Docker.

## Setup Instructions

### Prerequisites
- Install **Docker**
- Install **VS Code** with the **DevContainers extension**

### Running the Project
1. Clone the repository:
   ```sh
   git clone <repo-url>
   cd <repo-folder>
2. Open the project in VS Code.
3. When prompted, reopen in a DevContainer.
4. Once the container starts, the service will be ready to use.

## API Documentation

### Routes

#### Shopcarts
- `GET /shopcarts` - Lists all shopcarts grouped by user.

#### Shopcart operations

- `POST /shopcarts/{user_id}` - Adds an item to a user's shopcart or updates quantity if it already exists.
- `GET /shopcarts/{user_id}` - Retrieves the shopcart with metadata.
- `PUT /shopcarts/{user_id}` - Updates the entire shopcart.
- `DELETE /shopcarts/{user_id}` - Deletes the entire shopcart (all items).

#### ShopCart Items

- `POST /shopcarts/{user_id}/items` - Adds a product to a user's shopcart or updates quantity.
- `GET /shopcarts/{user_id}/items` - Lists all items in the user's shopcart (without metadata).

#### Specific Shopcart Item

- `GET /shopcarts/{user_id}/items/{item_id}` - Retrieves a specific item from the user's shopcart.
- `PUT /shopcarts/{user_id}/items/{item_id}` - Updates a specific item in the shopcart.
- `DELETE /shopcarts/{user_id}/items/{item_id}` - Removes an item from the shopcart.

#### Usage Examples

You can interact with the API using Postman, curl, or any similar tool.

- To **retrieve** a shopcart for a user with `user_id = 5` (with metadata):

```GET http://localhost:8080/shopcarts/5```

- To **list** all items in a user's shopcart:

```GET http://localhost:8080/shopcarts/5/items```

- To **add an item** to a user's shopcart, send a `POST` request with `JSON` data:
 
```POST http://localhost:8080/shopcarts/5```

```
json={
  "item_id": "123",
  "quantity": 2,
  "price": 9.99
}
```

- To **update** a specific item in the shopcart:

```PUT http://localhost:8080/shopcarts/5/items/123```

- To **delete** an item from the shopcart:

```DELETE http://localhost:8080/shopcarts/5/items/123```


## Kubernetes local development commands

Cluster initialization
```
make cluster
```

Build and tag
```
docker build -t shopcarts:latest .
docker tag shopcarts:latest cluster-registry:6000/shopcarts:latest

## If the docker push does not work add the following command
sudo bash -c "echo '127.0.0.1    cluster-registry' >> /etc/hosts"

docker push cluster-registry:6000/shopcarts:latest
```

Create namespace
```
kubectl create namespace dev
kns dev
```

Kubernetes Commands
```
kubectl apply -f k8s/pv.yaml

kubectl apply -f k8s/postgres/secret.yaml
kubectl apply -f k8s/postgres/stateful-set.yaml
kubectl apply -f k8s/postgres/pvc.yaml
kubectl apply -f k8s/postgres/service.yaml

# The following can also work
kubectl apply -f k8s/postgres/

kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

kubectl get all
kubectl get pods

## At this point, the service is running and can be accessed using the ingress at localhost:8080
## It takes a while to show in the kubectl get pods command but it is running

kubectl delete -f k8s/postgres/
kubectl delete -f k8s/

make cluster-rm
```

## License

Copyright (c) 2016, 2025 [John Rofrano](https://www.linkedin.com/in/JohnRofrano/). All rights reserved.

Licensed under the Apache License. See [LICENSE](LICENSE)

This repository is part of the New York University (NYU) masters class: **CSCI-GA.2820-001 DevOps and Agile Methodologies** created and taught by [John Rofrano](https://cs.nyu.edu/~rofrano/), Adjunct Instructor, NYU Courant Institute, Graduate Division, Computer Science, and NYU Stern School of Business.
