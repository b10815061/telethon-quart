# telethon-quart

To run the project, pull this repository

1. $git pull https://github.com/b10815061/telethon-quart

make sure to run a postgresql container with a sync configure(user,password, and database name) with ```telethon-quart\dbconfig.py```

2. docker run --name db -e POSTGRES_USER=tommy -e POSTGRES_PASSWORD=0000 -e POSTGRES_DB=telegram -v pg-data:/var/lib/postgresql/data -p 5432:5432 -d postgres:12-alpine

get to the directory of the repository (i.e.:telethon-quart)

3. $python main.py

nevigate to port:5000 on localhost
