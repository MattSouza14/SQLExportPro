 var editor = CodeMirror.fromTextArea(document.getElementById("sql_query"), {
        mode: "text/x-sql",
        theme: "eclipse",
        lineNumbers: true,
        extraKeys: {"Ctrl-Space": "autocomplete"},
        hintOptions: {
            tables: {}
        }
    });
    fetch("/autocomplete_metadata")
    .then(response => response.json())
    .then(data => {
        if (data.tables) {
            editor.options.hintOptions.tables = data.tables;
        }
    });
    
    editor.on("inputRead", function(cm, change) {
        if (change.text[0] === "." || change.text[0] === " ") {
            cm.showHint({completeSingle: false});
        }
    });

    function closeModal() {
    document.getElementById("resultModal").style.display = "none";
}

window.addEventListener("DOMContentLoaded", () => {
    const resultTable = document.getElementById("resultTableContainer");
    if (resultTable && resultTable.innerHTML.trim() !== "") {
        document.getElementById("resultModal").style.display = "block";
    }
});
