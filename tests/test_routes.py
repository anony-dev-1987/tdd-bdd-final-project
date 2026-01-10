######################################################################
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
######################################################################
"""
Product API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_service.py:TestProductService
"""
import os
import logging
from decimal import Decimal
from unittest import TestCase
from service import app
from service.common import status
from service.models import db, init_db, Product
from tests.factories import ProductFactory
from urllib.parse import quote_plus

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
# logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/products"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductRoutes(TestCase):
    """Product Service tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    ############################################################
    # Utility function to bulk create products
    ############################################################
    def _create_products(self, count: int = 1) -> list:
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, "Could not create test product"
            )
            new_product = response.get_json()
            test_product.id = new_product["id"]
            products.append(test_product)
        return products

    ############################################################
    #  T E S T   C A S E S
    ############################################################
    def test_index(self):
        """It should return the index page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Product Catalog Administration", response.data)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data['message'], 'OK')

    # ----------------------------------------------------------
    # TEST CREATE
    # ----------------------------------------------------------
    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

        #
        # Uncomment this code once READ is implemented
        #

        # Check that the location header was correct
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

    def test_create_product_with_no_name(self):
        """It should not Create a Product without a name"""
        product = self._create_products()[0]
        new_product = product.serialize()
        del new_product["name"]
        logging.debug("Product no name: %s", new_product)
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_no_content_type(self):
        """It should not Create a Product with no Content-Type"""
        response = self.client.post(BASE_URL, data="bad data")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_wrong_content_type(self):
        """It should not Create a Product with wrong Content-Type"""
        response = self.client.post(BASE_URL, data={}, content_type="plain/text")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    #
    # ADD YOUR TEST CASES HERE
    #

    # READ
    def test_get_product(self):
        """Test reading a product"""
        seed_products = self._create_products(count = 1)
        test_product = seed_products[0]
    
        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        product = response.get_json()
        self.assertEqual(product["name"], test_product.name)
        self.assertEqual(product["description"], test_product.description)
        self.assertEqual(Decimal(product["price"]), test_product.price)
        self.assertEqual(product["available"], test_product.available)
        self.assertEqual(product["category"], test_product.category.name)

    def test_get_product_not_found(self):
        """Test reading a product that does not exist"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # UPDATE
    def test_update_product(self):
        """Test updating a product"""
        seed_products = self._create_products(count = 1)
        seed_product = seed_products[0]
    
        response = self.client.get(f"{BASE_URL}/{seed_product.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        original_product = response.get_json()
        self.assertEqual(original_product["name"], seed_product.name)
        self.assertEqual(original_product["description"], seed_product.description)
        self.assertEqual(Decimal(original_product["price"]), seed_product.price)
        self.assertEqual(original_product["available"], seed_product.available)
        self.assertEqual(original_product["category"], seed_product.category.name)

        seed_product.name = "Updated Product Name"
        self.assertEqual(seed_product.name, "Updated Product Name")
        response = self.client.put(f"{BASE_URL}/{seed_product.id}", json=seed_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(f"{BASE_URL}/{seed_product.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated_product = response.get_json()
        self.assertEqual(updated_product["name"], seed_product.name)
        self.assertEqual(updated_product["description"], seed_product.description)
        self.assertEqual(Decimal(updated_product["price"]), seed_product.price)
        self.assertEqual(updated_product["available"], seed_product.available)
        self.assertEqual(updated_product["category"], seed_product.category.name)

    def test_update_product_not_found(self):
        """Test updating a product that does not exist"""
        response = self.client.put(f"{BASE_URL}/0", json={})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # DELETE
    def test_delete_product(self):
        """Test deleting a product"""
        seed_products = self._create_products(count = 1)
        seed_product = seed_products[0]
    
        response = self.client.delete(f"{BASE_URL}/{seed_product.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, b'')

    def test_delete_product_not_found(self):
        """Test deleting a product that does not exist"""
        response = self.client.delete(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # LIST
    def test_list_products(self):
        """Test listing products"""
        num = 10
        seed_products = self._create_products(count = num)
    
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        products = response.get_json()
        self.assertEqual(len(products), num)
        for product in products:
            matching_product = [seed_product for seed_product in seed_products if seed_product.id == product["id"]]
            self.assertEqual(len(matching_product), 1)
            reference_product = matching_product[0]
            self.assertEqual(product["name"], reference_product.name)
            self.assertEqual(product["description"], reference_product.description)
            self.assertEqual(Decimal(product["price"]), reference_product.price)
            self.assertEqual(product["available"], reference_product.available)
            self.assertEqual(product["category"], reference_product.category.name)

    def test_list_products_empty(self):
        """Test listing products when empty"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        products = response.get_json()
        self.assertEqual(len(products), 0)

    # LIST BY NAME
    def test_list_products_by_name(self):
        """Test listing products by name"""
        num = 10
        seed_products = self._create_products(count = num)
        target_product = seed_products[0]
        target_name = target_product.name
        target_count = sum(1 for product in seed_products if product.name == target_name)

        response = self.client.get(
            BASE_URL, query_string=f"name={quote_plus(target_name)}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        products = response.get_json()
        self.assertEqual(len(products), target_count)
        for product in products:
            self.assertEqual(product["name"], target_name)

    # LIST BY CATEGORY
    def test_list_products_by_category(self):
        """Test listing products by category"""
        num = 10
        seed_products = self._create_products(count = num)
        target_product = seed_products[0]
        target_category = target_product.category
        target_count = sum(1 for product in seed_products if product.category == target_category)

        response = self.client.get(
            BASE_URL, query_string=f"category={quote_plus(target_category.name)}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        products = response.get_json()
        self.assertEqual(len(products), target_count)
        for product in products:
            self.assertEqual(product["category"], target_category.name)

    # LIST BY AVAILABILITY
    def test_list_products_by_availability(self):
        """Test listing products by availability"""
        num = 10
        seed_products = self._create_products(count = num)
        target_product = seed_products[0]
        target_availability = target_product.available
        target_count = sum(1 for product in seed_products if product.available == target_availability)

        response = self.client.get(
            BASE_URL, query_string=f"available={quote_plus(str(target_availability))}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        products = response.get_json()
        self.assertEqual(len(products), target_count)
        for product in products:
            self.assertEqual(product["available"], target_availability)

    ######################################################################
    # Utility functions
    ######################################################################

    def get_product_count(self):
        """save the current number of products"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        # logging.debug("data = %s", data)
        return len(data)
