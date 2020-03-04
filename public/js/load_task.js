console.log("load_task");
function render_task(task, document) {
    console.log("rendering task:");
    console.log(task);
    var golds = document.getElementsByClassName("goldgraph");
    for (var i=0, len=golds.length|0; i<len; i=i+1|0) {
        golds[i].src = task["data"]["reference"];
    }
    document.getElementById("task_id").value = task["id"];
    document.getElementById("task_id_form").value = task["id"];
    document.getElementById("first").src = task["data"]["img_1"];
    document.getElementById("second").src = task["data"]["img_2"];
};

function set_selected_task(target) {
    return () => {
        document.getElementById("first_block").className = document.getElementById("first_block").className.replace(/ selected/g, "");
        document.getElementById("second_block").className = document.getElementById("second_block").className.replace(/ selected/g, "");
        document.getElementById(`${target}_block`).className += " selected";
        document.getElementById("answer").value = target;
        set_button_active("submit-btn")
    }
};

function set_button(btn, from, to) {
    document.getElementById(btn).className = document.getElementById(btn).className.replace(new RegExp(` ${from}`), "");
    document.getElementById(btn).className += ` ${to}`;
};

function set_button_active(btn) { document.getElementById(btn).removeAttribute("disabled"); }
function set_button_disabled(btn) {
    set_button(btn, "is-loading", "")
    document.getElementById(btn).setAttribute("disabled", "true");
}

function submitAnnotationData() {
    const task_id = document.getElementById("task_id_form");
    const answer = document.getElementById("answer");
    return {
        task_id: task_id.value,
        answer: answer.value
    }
};
