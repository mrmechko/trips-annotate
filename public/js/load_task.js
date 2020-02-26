console.log("load_task");
function render_task(task, document) {
    console.log("rendering task:");
    var golds = document.getElementsByClassName("goldgraph");
    for (var i=0, len=golds.length|0; i<len; i=i+1|0) {
        golds[i].src = task["reference"];
    }
    document.getElementById("first").src = task["img_1"];
    document.getElementById("second").src = task["img_2"];
    document.getElementById("test").src = task["id"];
};
