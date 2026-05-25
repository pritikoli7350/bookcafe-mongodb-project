from bson.objectid import ObjectId
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)

# 🔗 MongoDB Atlas connection
client = MongoClient("mongodb+srv://priti:priti.pk7350@cluster0.slwxkyd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["CafeDB"]
orders_collection = db["Orders"]

# Menu items
menu_items = [
    {"name": "Espresso", "price": 80},
    {"name": "Cappuccino", "price": 120},
    {"name": "Latte", "price": 150},
    {"name": "Mocha", "price": 170},
]

# In-memory order (resets on restart)
current_order = []


@app.route("/")
def menu():
    return render_template("menu.html", menu=menu_items)


@app.route("/add_to_order", methods=["POST"])
def add_to_order():
    selected_items = request.form.getlist("item_name")  # multiple selected
    quantities = request.form.getlist("quantity")       # parallel list

    for item, qty in zip(selected_items, quantities):
        if int(qty) > 0:  # only add if qty > 0
            # find price of this item
            price = next((m["price"] for m in menu_items if m["name"] == item), None)
            if price:
                for _ in range(int(qty)):
                    current_order.append({"name": item, "price": price})

    return redirect(url_for("show_order"))


@app.route("/remove_from_order/<int:index>")
def remove_from_order(index):
    if 0 <= index < len(current_order):
        current_order.pop(index)
    return redirect(url_for("show_order"))


@app.route("/order")
def show_order():
    total = sum(item["price"] for item in current_order)
    return render_template("order.html", order=current_order, total=total)


@app.route("/place_order", methods=["POST"])
def place_order():
    if current_order:
        order_document = {
            "order": current_order.copy(),
            "total": sum(item["price"] for item in current_order)
        }
        orders_collection.insert_one(order_document)
        current_order.clear()
        return render_template("order_success.html")
    return render_template("order_success.html", message="⚠️ No items in order!")


@app.route("/admin")
def admin_panel():
    all_orders = list(orders_collection.find())
    return render_template("admin.html", orders=all_orders)


@app.route("/admin/delete/<order_id>")
def delete_order(order_id):
    orders_collection.delete_one({"_id": ObjectId(order_id)})
    return redirect(url_for("admin_panel"))


@app.route("/admin/edit/<order_id>", methods=["GET", "POST"])
def edit_order(order_id):
    order = orders_collection.find_one({"_id": ObjectId(order_id)})
    if request.method == "POST":
        updated_items = []
        names = request.form.getlist("item_name")
        prices = request.form.getlist("item_price")
        for n, p in zip(names, prices):
            if n.strip() != "":
                updated_items.append({"name": n, "price": int(p)})
        updated_total = sum(item["price"] for item in updated_items)
        orders_collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"order": updated_items, "total": updated_total}}
        )
        return redirect(url_for("admin_panel"))
    return render_template("edit_order.html", order=order)


if __name__ == "__main__":
    app.run(debug=True)
