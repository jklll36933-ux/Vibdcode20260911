"""SQLite CRUD example for product data."""

import sqlite3
from contextlib import contextmanager
from typing import Iterator, List, Tuple


DB_FILE = "products.db"
Product = Tuple[int, str, int]


@contextmanager
def open_database() -> Iterator[sqlite3.Connection]:
    """Open a database connection and always close it after use."""
    connection = sqlite3.connect(DB_FILE)
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def create_table() -> None:
    """Create the Products table when it does not exist."""
    with open_database() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS Products (
                productID INTEGER PRIMARY KEY AUTOINCREMENT,
                productName TEXT NOT NULL,
                productPrice INTEGER NOT NULL
            )
            """
        )


def insert_product(product_name: str, product_price: int) -> int:
    """Insert a product and return its generated productID."""
    with open_database() as connection:
        cursor = connection.execute(
            "INSERT INTO Products (productName, productPrice) VALUES (?, ?)",
            (product_name, product_price),
        )
        return cursor.lastrowid


def update_product(product_id: int, product_name: str, product_price: int) -> bool:
    """Update a product and return whether a row was changed."""
    with open_database() as connection:
        cursor = connection.execute(
            """
            UPDATE Products
            SET productName = ?, productPrice = ?
            WHERE productID = ?
            """,
            (product_name, product_price, product_id),
        )
        return cursor.rowcount > 0


def delete_product(product_id: int) -> bool:
    """Delete a product and return whether a row was deleted."""
    with open_database() as connection:
        cursor = connection.execute(
            "DELETE FROM Products WHERE productID = ?",
            (product_id,),
        )
        return cursor.rowcount > 0


def search_products(product_name: str = "") -> List[Product]:
    """Return products whose names contain the search text."""
    with open_database() as connection:
        cursor = connection.execute(
            """
            SELECT productID, productName, productPrice
            FROM Products
            WHERE productName LIKE ?
            ORDER BY productID
            """,
            (f"%{product_name}%",),
        )
        return cursor.fetchall()


def print_products(products: List[Product]) -> None:
    """Print product rows in a readable format."""
    if not products:
        print("검색 결과가 없습니다.")
        return

    print("\nID | 상품명 | 가격")
    print("-" * 30)
    for product_id, product_name, product_price in products:
        print(f"{product_id} | {product_name} | {product_price:,}원")


def read_price(prompt: str) -> int:
    """Read a non-negative integer price from the user."""
    while True:
        try:
            price = int(input(prompt))
            if price < 0:
                raise ValueError
            return price
        except ValueError:
            print("가격은 0 이상의 정수로 입력하세요.")


def read_product_id() -> int:
    """Read a product ID from the user."""
    while True:
        try:
            product_id = int(input("상품 ID: "))
            if product_id <= 0:
                raise ValueError
            return product_id
        except ValueError:
            print("상품 ID는 양의 정수로 입력하세요.")


def run_menu() -> None:
    """Run the interactive product management menu."""
    create_table()

    while True:
        print(
            "\n[상품 관리]"
            "\n1. 상품 입력"
            "\n2. 상품 수정"
            "\n3. 상품 삭제"
            "\n4. 상품 검색"
            "\n5. 전체 상품 조회"
            "\n0. 종료"
        )
        choice = input("선택: ").strip()

        if choice == "1":
            product_name = input("상품명: ").strip()
            if not product_name:
                print("상품명을 입력하세요.")
                continue
            product_price = read_price("가격: ")
            product_id = insert_product(product_name, product_price)
            print(f"상품이 입력되었습니다. 생성된 상품 ID: {product_id}")
        elif choice == "2":
            product_id = read_product_id()
            product_name = input("새 상품명: ").strip()
            if not product_name:
                print("상품명을 입력하세요.")
                continue
            product_price = read_price("새 가격: ")
            if update_product(product_id, product_name, product_price):
                print("상품이 수정되었습니다.")
            else:
                print("해당 상품을 찾을 수 없습니다.")
        elif choice == "3":
            product_id = read_product_id()
            if delete_product(product_id):
                print("상품이 삭제되었습니다.")
            else:
                print("해당 상품을 찾을 수 없습니다.")
        elif choice == "4":
            keyword = input("검색할 상품명: ").strip()
            print_products(search_products(keyword))
        elif choice == "5":
            print_products(search_products())
        elif choice == "0":
            print("프로그램을 종료합니다.")
            break
        else:
            print("메뉴 번호를 올바르게 선택하세요.")


if __name__ == "__main__":
    run_menu()
