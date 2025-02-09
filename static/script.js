let uploadedFiles = { fileInput1: false, fileInput2: false, fileInput3: false }; 
let generatedRules = { rulesTable1: false, rulesTable2: false, rulesTable3: false }; 

function updateButtons() {
    document.getElementById("generateAll").disabled = !Object.values(uploadedFiles).every(Boolean);  
    document.getElementById("findMaxRules").disabled = !Object.values(generatedRules).every(Boolean); 

    document.getElementById("generateTree1").disabled = !generatedRules["rulesTable1"];
    document.getElementById("generateTree2").disabled = !generatedRules["rulesTable2"];
    document.getElementById("generateTree3").disabled = !generatedRules["rulesTable3"];
}

function uploadFile(input, tableId) {
    let file = input.files[0]; 
    if (!file) return;

    let formData = new FormData(); 
    formData.append("file", file);
    formData.append("tableId", tableId);

    fetch("/upload", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) { 
            displayCSV(data.data, tableId);
            uploadedFiles[input.id] = true;
            updateButtons(); 
        } else {
            alert("Błąd podczas wgrywania pliku: " + data.message);
        }
    });
}

function generateAllRules() {
    let tables = ["dataTable1", "dataTable2", "dataTable3"];
    let rulesTables = ["rulesTable1", "rulesTable2", "rulesTable3"];

    tables.forEach((tableId, index) => {
        generateRules(tableId, rulesTables[index]);
    });
}

function generateRules(tableId, rulesTableId) {
    let fileKey = tableId.replace("dataTable", "reduct"); 
    let messageId = rulesTableId.replace("rulesTable", "rulesMessage"); 

    fetch("/generate_rules", {
        method: "POST",
        body: JSON.stringify({ tableId: fileKey }), 
        headers: { "Content-Type": "application/json" }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            let table = document.getElementById(rulesTableId);
            table.innerHTML = "<tr><th>#</th><th>Reguły</th></tr>"; 

            data.rules.forEach((rule, index) => {
                let row = `<tr><td>${index + 1}</td><td>${rule[0]}</td></tr>`; 
                table.innerHTML += row;
            });
            
            document.getElementById(messageId).style.display = "block";

            if (document.getElementById("rulesMessage1").style.display === "block" &&
                document.getElementById("rulesMessage2").style.display === "block" &&
                document.getElementById("rulesMessage3").style.display === "block") {
                document.getElementById("globalRulesMessage").style.display = "block";
                document.getElementById("findMaxRules").disabled = false;
            }
            
            generatedRules[rulesTableId] = true; 
            updateButtons(); 
        } else {
            alert("Błąd podczas generowania reguł: " + data.message);
        }
    });
}

function displayCSV(csvData, tableId) {
    let table = document.getElementById(tableId);
    table.innerHTML = ""; 

    let thead = "<tr><th>#</th>";
    csvData[0].forEach(header => thead += `<th>${header}</th>`);
    thead += "</tr>";
    table.innerHTML += thead;

    let tbody = "";
    for (let i = 1; i < csvData.length; i++) {
        tbody += `<tr><td>${i}</td>`;
        csvData[i].forEach(cell => tbody += `<td>${cell}</td>`);
        tbody += "</tr>";
    }
    table.innerHTML += tbody;
}

function findMaxRules() {
    fetch("/find_max_rules", { method: "POST" })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById("maxRulesContainer").style.display = "block";
            document.getElementById("maxRulesOutput").textContent = data.output;

            document.getElementById("maxRulesMessage").style.display = "block";
        } else {
            alert("Błąd: " + data.message);
        }
    });
}

function generateDecisionTree(reductNumber) {
    fetch("/generate_tree", {
        method: "POST",
        body: JSON.stringify({ reduct: `dataTable${reductNumber}` }),
        headers: { "Content-Type": "application/json" }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            let imgElement = document.getElementById(`treeImage${reductNumber}`);
            let treeContainer = document.getElementById(`treeContainer${reductNumber}`);

            imgElement.src = data.image_path;
            imgElement.style.display = "block";
            treeContainer.style.display = "block"; 
        } else {
            alert("Błąd podczas generowania drzewa: " + data.message);
        }
    });
}