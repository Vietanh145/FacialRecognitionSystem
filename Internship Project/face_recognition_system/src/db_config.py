from cloudinary import config

DB_CONFIG = {
    'dbname': 'users_system',
    'user': 'postgres',
    'password': '123456',
    'host': 'localhost',
    'port': '5432'
}

# Configure Cloudinary
CLOUDINARY_CONFIG = {
    'cloud_name': 'user_images',
    'api_key': '428861531223223',
    'api_secret': 'i_0UUA9rXZUnzTHF5ODXg2FfvKM'
}

# Initialize Cloudinary configuration
config(**CLOUDINARY_CONFIG)