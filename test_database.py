
from database import execute_query

# Check the total number of products
result = execute_query(
    "SELECT COUNT(*) AS total_products FROM products"
)
print("Total products:", result[0]["total_products"])

# Show three sample products
products = execute_query(
    "SELECT product_name, brand, selling_price_INR "
    "FROM products LIMIT 3"
)

for product in products:
    print(product)

from database import execute_query

results = execute_query("""
    SELECT common_color, color, color_filled, product_name
    FROM products
    WHERE LOWER(common_color) = 'blue'
    LIMIT 15
""")

for row in results:
    print(row)
