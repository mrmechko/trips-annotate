function render_task(task, document) {
    console.log("rendering task:");
    console.log(task);
    var reference = task["data"]["reference"];
    const ref = (id) => `${reference}${id}.svg?sanitize=true`;
    document.getElementById("sentence").innerHTML = task["data"]["sentence"];
    document.getElementById("task_id").value = task["id"];
    document.getElementById("task_id_form").value = task["id"];
    document.getElementById("first").src = ref("first")
    document.getElementById("gold_first").src = ref("gold_first")
    document.getElementById("second").src = ref("second")
    document.getElementById("gold_second").src = ref("gold_second")
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

function set_other_response() {
    return () => {
        document.getElementById("first_block").className = document.getElementById("first_block").className.replace(/ selected/g, "");
        document.getElementById("second_block").className = document.getElementById("second_block").className.replace(/ selected/g, "");
        const target = document.getElementById("other_menu").value;
        document.getElementById("answer").value = target;
        if (target === "error_text") {//Do stuff here
            document.getElementById("other_response").disabled = false;
            set_button_disabled("submit-btn")
        } else {
            document.getElementById("other_response").disabled = true;
            set_button_active("submit-btn")
        }
    }
};

function reason_provided(target) {
    return () => {
        if (document.getElementById(target).value.length > 3) {
            set_button_active("submit-btn")
        } else {
            set_button_disabled("submit-btn")
        }
    }
}

function set_button(btn, from, to) {
    document.getElementById(btn).className = document.getElementById(btn).className.replace(new RegExp(` ${from}`), "");
    document.getElementById(btn).className += ` ${to}`;
};

function set_button_active(btn) {
    set_button(btn, "is-dark", "is-primary")
    document.getElementById(btn).removeAttribute("disabled");
}

function set_button_disabled(btn) {
    set_button(btn, "is-primary", "is-dark")
    set_button(btn, "is-loading", "")
    document.getElementById(btn).setAttribute("disabled", "true");
}

function submitAnnotationData() {
    const task_id = document.getElementById("task_id_form");
    const answer = document.getElementById("answer");
    const meta = (answer == "error") ? document.getElementById("other_response").value : "";
    return {
        task_id: task_id.value,
        answer: answer.value,
        meta: meta
    }
};
