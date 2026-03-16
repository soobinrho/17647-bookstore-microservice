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

### Plan (delete this section after I complete everything)

1. Locally create a FastAPI service and meet all the specs required by Professor Merson's specifications. Since the SQL server will not be Dockerized and will be spawned as AWS Aurora MySQL servers, just use `print("TODO: DUMMY DATA")` so that I don't have to worry about reads and writes for the DB. For now, finish setting up all the required API endpoints, status code handling, and error handling. In the same way, just use a dummy function `def get_book_summary_from_llm(book_name: str, book_author: str) -> str` with a `print("500 WORDS SUMMARY OF BOOK. TOOD: Replace with actual LLM API call.")` for now.

2. Finish the code for the DB reads and writes using a local MariaDB instance deployed on Docker. This will not go to the final version of the assignment. The final version will use the AWS Aurora MySQL instances, so the local instance is just for writing and testing.

3. Write the LLM code. Prompt should be `You're Frank Herbert the author of Dune. I am a huge fan of yours. Please write a 500-word summary of the following book: {book_name} by the author {book_author}. I don't care if the book actually exists or not, so please feel free to make up something based on the book name and the book author. Please respond with a summary of the book in exactly 500 words.`

4. Dockerize.

5. Deploy the FastAPI service to EC2 instances. Figure out a secure way to set the creds for the DB instances (maybe `.env` files).

<br>
