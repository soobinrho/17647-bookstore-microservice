def main():
    pass
    # [TODO]
    # 0. Create K8s yaml first to figure out how cronjob works in K8s.
    #    N = 60 seconds. It should use the env var SYNC_DATA_PERIOD_SECONDS
    # 1. Create a new column called last_updated_time_unix_epoch with bigint
    # 2. Read all books ISBN and their last_updated_time_unix_epoch
    # 3. Create new MongoDB collection if not exists.
    # 4. Go through each MongoDB and update everything that's outdated
    #    according to last_updated_time_unix_epoch.


if __name__ == "__main__":
    main()


# echo ${DB_BOOKS_COMMANDS_URL}
# echo ${DB_BOOKS_COMMANDS_PORT}
# echo ${DB_BOOKS_COMMANDS_USER}
# echo ${DB_BOOKS_COMMANDS_PASS}
# echo ${DB_BOOKS_COMMANDS_DATABASE}

# echo ${DB_BOOKS_QUERIES_URL}
# echo ${DB_BOOKS_QUERIES_PORT}
# echo ${DB_BOOKS_QUERIES_USER}
# echo ${DB_BOOKS_QUERIES_PASS}
# echo ${DB_BOOKS_QUERIES_DATABASE}

# echo ${SYNC_DATA_PERIOD_SECONDS}

# mongosh --host ${DB_BOOKS_QUERIES_URL} \
#   --port ${DB_BOOKS_QUERIES_PORT} \
#   --username ${DB_BOOKS_QUERIES_USER} \
#   --password ${DB_BOOKS_QUERIES_PASS}

# [TODO] Use MongoDB Relational Migrator.
#
# https://www.mongodb.com/docs/relational-migrator/installation/install-with-docker/
# docker pull public.ecr.aws/v4d7k6c9/relational-migrator:latest
# docker run --name mongodb-relational-migrator -p 8080:8080 public.ecr.aws/v4d7k6c9/relational-migrator:latest

# I'll probably have to create a new Dockerfile because it requires
# DB driver. I'll have to obtain MySQL driver and install it at the docker image.

# [TODO] Figure out how to run headless. -e something=True

# CHECK OUT https://www.mongodb.com/docs/relational-migrator/api-docs/
# WHERE DATEDIFF(CURDATE(), last_modified) <= 1
#
# CHECK OUT https://www.mongodb.com/docs/api/doc/mongodb-relational-migrator-rest-api/operation/operation-getjob

# REFERENCE: https://www.mongodb.com/community/forums/t/i-setup-replication-between-mysql-and-mongodb-using-relational-migrator/262966
# "Have you select as migration options the flag continuous?"
#
# [NOTE] Alternatively, just do it in PYthon. It will be easy enough and might actually
# be the most suitable way in this use case. Just like the CRM service.
# Don't name it service though. It should just be a cronjob-type of Python script.
