# Assignment 1: Bookstore

`17647-D4 | 2026 | Professor Paulo Merson | Soobin Rho`

<br>

A bookstore backend built in the microservice architecture.

| Service Purpose | Where & How |
| --------------- | ----------- |
| **API Service** | Python FastAPI deployed on two instances of AWS EC2 for better availability. |
| **Database** | MySQL deployed on two instances of AWS Aurora MySQL. |
| **LLM for Summary of Books** | External API calls to Genmini. |

<br>

### Notes for my future self

Professor Merson provided a CloudFormation template for all of our assignments, so provisioning of EC2 instances, Aurora MySQL instances, and network & security configurations has already been automated.
Remember, one disadvantage of the microservice architecture compared to the monolithic architecture is that deployment in microservice can get more convoluted, solution of which is automation of deployment.

Don't deploy microservice systems manually unless absolutely necessary (e.g. testing and debugging).
This was a fun assignment as it was my first time deploying a proper microservice system and also happend to be my first time deploying to AWS.
Up to this point, I only had experience with Hetzner and DigitalOcean.

<br>

### Lessons learned for my future self

- **CloudFormation Setup**: When we upload the CloudFormation template to AWS, it will ask us to set the credentials for the database and also IP allowlisting for the SSH service at the EC2 instances. By default, `0.0.0.0/0` is allowed for SSH, so make sure to change this to my IP for security.

- **Docker Tag**: `docker tag "soobinrho/17647-A1-bookstore-microservice:$(git rev-parse --short HEAD)"` to set the tag name as the current git commit hash.

<br>
