import streamlit as st
from quick_webapp import bean, session_bean
from quick_webapp.webapp import menu_page
from quick_webapp.ui.page_context import PageContext
from quick_webapp.ui.action_table import action_table
from context import webapp

class OrderExample:
    def __init__(self, title: str, amount: int, price: float):
        self.__title = title
        self.__amount = amount
        self.__price = price

    @property
    def title(self) -> str:
        return self.__title

    @property
    def amount(self) -> int:
        return self.__amount

    @amount.setter
    def amount(self, value: int):
        self.__amount = value

    @property
    def price(self) -> float:
        return self.__price

def __edit(order: OrderExample, page_context: PageContext):
    order.amount += 1
    page_context.put_notification(f"I am sorta edited order '{order.title}' placing one additional item", "📢")

def __delete(order: OrderExample, page_context: PageContext):
    order.amount -= order.amount
    page_context.put_notification(f"I am sorta deleted order '{order.title}', setting amount to 0", "🚨")

@bean(key="action_table_example_data_mappers")
def __data_mappers() -> dict[str, callable]:
    return {
        "Title": lambda o: st.write(o.title),
        "Amount": lambda o: st.write(f"{o.amount}"),
        "Price": lambda o: st.write(f"${o.price:.2f}"),
        "Total": lambda o: st.write(f"${o.amount * o.price:.2f}")
    }

@session_bean(key="action_table_example_action_mappers")
def __action_mappers() -> dict[str, callable]:
    return {
        "Edit": lambda order: __edit(order, page_context),
        "Delete": lambda order: __delete(order, page_context)
    }

@session_bean(key="action_table_example_page_context")
def __page_context() -> PageContext:
    return PageContext(
        "action_table_example",
        default_context={
            "orders": [
                OrderExample("Apple", 3, 1.25),
                OrderExample("Banana", 5, 0.80),
                OrderExample("Orange", 2, 1.60)
            ]
        }
    )

menu_page("1_UIs", "3_Action table")
with webapp().as_context("UI | Action Table Example"):
    page_context = __page_context()
    st.write("**Orders:**")

    action_table(
            data=__page_context().get_context()["orders"],
            no_data_message="No orders...",
            data_mappers=__data_mappers(),
            action_mappers=__action_mappers(),
            actions_col_label="Actions",
            column_ratio_spec=[6, 2, 2, 1, 1],
            container_width=1000
    )

    page_context.fire_notifications("app")