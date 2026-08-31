# BhuDrishti 3D Database

## Setup PostgreSQL + PostGIS locally
1. Install PostgreSQL and PostGIS.
2. `CREATE DATABASE bhudrishti3d;`
3. `\c bhudrishti3d`
4. `CREATE EXTENSION postgis;`
5. Run `psql -d bhudrishti3d -f schema.sql`
6. Run `psql -d bhudrishti3d -f seed_demo.sql`
