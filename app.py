from flask import Flask, request, jsonify, render_template 
import pandas as pd 
import os 
import matplotlib
matplotlib.use('Agg')  
from sklearn.tree import DecisionTreeClassifier, _tree, plot_tree 
import uuid 
import matplotlib.pyplot as plt 

app = Flask(__name__) 
UPLOAD_FOLDER = "uploads" 
RULES_FOLDER = "rules" 

uploaded_files = {}

@app.route("/") 
def index():
    return render_template("index.html") 

@app.route("/upload", methods=["POST"])
def upload():
    
    if "file" not in request.files or "tableId" not in request.form:
        return jsonify({"success": False, "message": "Błąd przesyłania pliku!"})

    file = request.files["file"]
    table_id = request.form["tableId"]
    
    unique_filename = f"{uuid.uuid4()}_{file.filename}" 
    file_path = os.path.join(UPLOAD_FOLDER, unique_filename) 
    file.save(file_path) 

    uploaded_files[table_id] = unique_filename  

    df = pd.read_csv(file_path)
    data = [df.columns.tolist()] + df.values.tolist()
    return jsonify({"success": True, "data": data})

def extract_rules_as_linear(tree, feature_names): 
    def recurse(node, conditions): 
        if tree.feature[node] != _tree.TREE_UNDEFINED: 
            
            feature = feature_names[tree.feature[node]] 
            threshold = tree.threshold[node] 

            left_conditions = conditions + [f"{feature} <= {threshold:.2f}"] 
            recurse(tree.children_left[node], left_conditions) 

            right_conditions = conditions + [f"{feature} > {threshold:.2f}"]
            recurse(tree.children_right[node], right_conditions)
        else:
            decision = tree.value[node].argmax() 
            rule = " AND ".join(conditions) + f" => class: {decision}" 
            rules.append(rule) 

    rules = [] 
    recurse(0, []) 
    return rules

@app.route("/generate_rules", methods=["POST"])
def generate_rules():
    data = request.get_json()
    table_id = data.get("tableId").replace("reduct", "dataTable")  

    if table_id not in uploaded_files:
        return jsonify({"success": False, "message": "Brak wgranego pliku dla tego reduktu!"})

    file_path = os.path.join(UPLOAD_FOLDER, uploaded_files[table_id])
    if not os.path.exists(file_path):
        return jsonify({"success": False, "message": "Brak pliku wejściowego!"})

    df = pd.read_csv(file_path)
    if df.shape[1] < 2:
        return jsonify({"success": False, "message": "Plik musi zawierać co najmniej dwie kolumny!"})

    X = df.iloc[:, :-1] 
    y = df.iloc[:, -1] 

    clf = DecisionTreeClassifier(criterion="entropy", random_state=42).fit(X, y)

    rules = extract_rules_as_linear(clf.tree_, list(X.columns))

    rules_path = os.path.join(RULES_FOLDER, f"{table_id}_rules.txt")
    with open(rules_path, "w") as f:
        f.writelines("\n".join(rules))

    return jsonify({"success": True, "rules": [[f"{i + 1}. {rule}"] for i, rule in enumerate(rules)]})

def load_rules_from_files():
    
    file_paths = [
        os.path.join("rules", "dataTable1_rules.txt"),
        os.path.join("rules", "dataTable2_rules.txt"),
        os.path.join("rules", "dataTable3_rules.txt")
    ]

    all_rules = []
    for file_index, file_path in enumerate(file_paths): 
        if os.path.exists(file_path):
            tree_name = f"Tree{file_index + 1}" 
            with open(file_path, "r", encoding="utf-8") as f: 
                rules = f.readlines() 
                for rule in rules:
                    if "=>" in rule: 
                        all_rules.append((rule.strip(), tree_name))
    return all_rules 

def is_rule_true_for_tree(rule, tree_rules): 
    """Sprawdza, czy reguła jest prawdziwa dla danego drzewa"""
    for r_prime in tree_rules:
        rule_parts = rule.split("=>") 
        r_prime_parts = r_prime.split("=>")

        if len(rule_parts) == 2 and len(r_prime_parts) == 2: 
            C_r, D_r = rule_parts[0].strip(), rule_parts[1].strip() 
            C_r_prime, D_r_prime = r_prime_parts[0].strip(), r_prime_parts[1].strip() 

            if D_r == D_r_prime and C_r_prime in C_r:
                return True
    return False

def find_rules_for_max_trees(all_rules):
    """Znajduje reguły spełnione dla maksymalnej liczby drzew"""
    unique_rules = {rule for rule, _ in all_rules} 
    rule_validity = {rule: 0 for rule in unique_rules} 

    for rule in unique_rules:
        for tree_name in set(tree for _, tree in all_rules): 
            tree_rules = [r for r, t in all_rules if t == tree_name] 
            if is_rule_true_for_tree(rule, tree_rules):
                rule_validity[rule] += 1

    max_trees = max(rule_validity.values(), default=0) 
    rules_for_max_trees = [rule for rule, count in rule_validity.items() if count == max_trees] 
    return rules_for_max_trees, max_trees

@app.route("/find_max_rules", methods=["POST"])
def find_max_rules():
   
    file_paths = [
        os.path.join("rules", "dataTable1_rules.txt"),
        os.path.join("rules", "dataTable2_rules.txt"),
        os.path.join("rules", "dataTable3_rules.txt")
    ]

    if not all(os.path.exists(path) for path in file_paths):
        return jsonify({"success": False, "message": "Nie wszystkie pliki z regułami zostały wygenerowane!"})

    all_rules = load_rules_from_files()
    rules_for_max_trees, max_trees = find_rules_for_max_trees(all_rules)

    output = f"Reguły prawdziwe dla maksymalnej liczby drzew ({max_trees}):\n\n" + "\n".join(rules_for_max_trees)

    with open("IR_S_results.txt", "w", encoding="utf-8") as f:
        f.write(output)

    return jsonify({"success": True, "output": output})

@app.route("/generate_tree", methods=["POST"])
def generate_tree():
    data = request.get_json()
    table_id = data.get("reduct")

    if table_id not in uploaded_files:
        return jsonify({"success": False, "message": "Brak wgranego pliku dla tego reduktu!"})

    file_path = os.path.join(UPLOAD_FOLDER, uploaded_files[table_id])
    if not os.path.exists(file_path):
        return jsonify({"success": False, "message": "Brak pliku wejściowego!"})

    df = pd.read_csv(file_path)
    if df.shape[1] < 2:
        return jsonify({"success": False, "message": "Plik musi zawierać co najmniej dwie kolumny!"})

    X = df.iloc[:, :-1]  
    y = df.iloc[:, -1]   

    clf = DecisionTreeClassifier(criterion="entropy", random_state=42).fit(X, y)

    plt.figure(figsize=(20, 12)) 
    plot_tree(clf, feature_names=list(X.columns), class_names=True, filled=True)
    
    image_filename = f"tree_{table_id}.png"
    image_path = os.path.join("static", image_filename)
    plt.savefig(image_path, dpi=300)
    plt.close('all') 

    return jsonify({"success": True, "image_path": f"/static/{image_filename}"})


if __name__ == "__main__":
    app.run(debug=True)
