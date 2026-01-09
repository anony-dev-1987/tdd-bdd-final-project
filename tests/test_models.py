# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db
from service import app
from tests.factories import ProductFactory
logger = logging.getLogger("test_models")

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        logging.getLogger('faker').setLevel(logging.ERROR)
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    #
    # ADD YOUR TEST CASES HERE
    #

    def test_read_a_product(self):
        """Test reading a product"""
        seed_product = ProductFactory()
        logger.info("Creating product: %s", seed_product)

        seed_product.id = None
        seed_product.create()

        self.assertIsNotNone(seed_product.id)

        product = Product.find(seed_product.id)

        self.assertEqual(product.id, seed_product.id)
        self.assertEqual(product.name, seed_product.name)
        self.assertEqual(product.description, seed_product.description)
        self.assertEqual(product.price, seed_product.price)
        self.assertEqual(product.available, seed_product.available)
        self.assertEqual(product.category, seed_product.category)

    def test_update_a_product(self):
        """Test reading a product"""
        seed_product = ProductFactory()
        logger.info("Creating product: %s", seed_product)

        seed_product.id = None
        seed_product.create()

        self.assertIsNotNone(seed_product.id)

        logger.info("Created product: %s", seed_product)

        seed_product.description = "foo"
        old_id = seed_product.id

        seed_product.update()

        self.assertEqual(seed_product.id, old_id)
        self.assertEqual(seed_product.description, "foo")

        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, old_id)
        self.assertEqual(products[0].description, seed_product.description)

    def test_delete_a_product(self):
        """Test deleting a product"""
        seed_product = ProductFactory()
        logger.info("Creating product: %s", seed_product)
        seed_product.create()

        products = Product.all()
        self.assertEqual(len(products), 1)

        seed_product.delete()

        products = Product.all()
        self.assertEqual(len(products), 0)

    def test_list_all_products(self):
        """Test listing all products"""
        products = Product.all()
        self.assertEqual(len(products), 0)

        for _ in range(5):
            seed_product = ProductFactory()
            seed_product.create()

        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_find_product_by_name(self):
        """Test finding a product by name"""
        products = Product.all()
        self.assertEqual(len(products), 0)

        num = 5
        for _ in range(num):
            seed_product = ProductFactory()
            seed_product.create()

        products = Product.all()
        self.assertEqual(len(products), num)

        find_name = products[0].name
        count = sum(1 for product in products if product.name == find_name)

        found_products = Product.find_by_name(find_name)
        self.assertEqual(found_products.count(), count)
        for product in found_products:
            self.assertEqual(product.name, find_name)

    def test_find_product_by_availability(self):
        """Test finding a product by availability"""
        products = Product.all()
        self.assertEqual(len(products), 0)

        num = 10
        for _ in range(num):
            seed_product = ProductFactory()
            seed_product.create()

        products = Product.all()
        self.assertEqual(len(products), num)

        find_available = products[0].available
        count = sum(1 for product in products if product.available == find_available)

        found_products = Product.find_by_availability(find_available)
        self.assertEqual(found_products.count(), count)
        for product in found_products:
            self.assertEqual(product.available, find_available)

    def test_find_product_by_category(self):
        """Test finding a product by category"""
        products = Product.all()
        self.assertEqual(len(products), 0)

        num = 10
        for _ in range(num):
            seed_product = ProductFactory()
            seed_product.create()

        products = Product.all()
        self.assertEqual(len(products), num)

        find_category = products[0].category
        count = sum(1 for product in products if product.category == find_category)

        found_products = Product.find_by_category(find_category)
        self.assertEqual(found_products.count(), count)
        for product in found_products:
            self.assertEqual(product.category, find_category)

    def test_find_product_by_price(self):
        """Test finding a product by price"""
        products = Product.all()
        self.assertEqual(len(products), 0)

        num = 10
        for _ in range(num):
            seed_product = ProductFactory()
            seed_product.create()

        products = Product.all()
        self.assertEqual(len(products), num)

        find_price = products[0].price
        count = sum(1 for product in products if product.price == find_price)

        found_products = Product.find_by_price(find_price)
        self.assertEqual(found_products.count(), count)
        for product in found_products:
            self.assertEqual(product.price, find_price)

    def test_find_product_by_string_price(self):
        """Test finding a product by price"""
        products = Product.all()
        self.assertEqual(len(products), 0)

        num = 10
        for _ in range(num):
            seed_product = ProductFactory()
            seed_product.create()

        products = Product.all()
        self.assertEqual(len(products), num)

        find_price = products[0].price
        count = sum(1 for product in products if product.price == find_price)

        found_products = Product.find_by_price(str(find_price))
        self.assertEqual(found_products.count(), count)
        for product in found_products:
            self.assertEqual(product.price, find_price)
