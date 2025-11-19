import redis

redis_client = redis.Redis(
    host='redis-12014.c10.us-east-1-4.ec2.cloud.redislabs.com',
    port=12014,
    decode_responses=True,
    username="default",
    password="uivvsXBF64qgDagCC9j4EErUFE74CAsq",
)