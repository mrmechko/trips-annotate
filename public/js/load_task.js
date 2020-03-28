function render_a_b_parse(task, document) {
    //console.log("rendering task:");
    //console.log(task);
    var reference = task["data"]["reference"];

    const ref = (id) => `${reference}${id}.svg?sanitize=true`;
    var general = document.getElementById("task_box").innerHTML;
    var template = document.getElementById("a_b_parse").innerHTML;
    var rendered = Mustache.render(general, {
        sentence: task.sentence,
        task_id: task.id,
        parses: Mustache.render(template, {
               tasks: [
                   {option_id: "first", candidate: ref("first"), gold: ref("gold_first")},
                   {option_id: "second", candidate: ref("second"), gold: ref("gold_second")}
               ]
        })
    });
    document.getElementById("task_id_form").value = task["id"];

    document.getElementById("target").innerHTML = rendered;

    document.getElementById("option_first").addEventListener("click", set_selected_task("first", document));
    document.getElementById("option_second").addEventListener("click", set_selected_task("second", document));

};

function render_pick_gold(task, document) {
    var reference = task["data"]["reference"];

    const ref = (id) => `${reference}${id}.svg?sanitize=true`;
    // Data is a list of indexes of parses
    const tasks = task["data"]["data"].map((v, i) => {
        return {
            option_id: i, candidate: ref(v)
        }

    })
    var general = document.getElementById("task_box").innerHTML;
    var template = document.getElementById("pick_gold").innerHTML;
    var rendered = Mustache.render(general, {
        sentence: task.sentence,
        task_id: task.id,
        parses: Mustache.render(template, {
            tasks: tasks
        })
    });
    document.getElementById("task_id_form").value = task["id"];
    document.getElementById("target").innerHTML = rendered;

    for (i = 0; i < tasks.length; i++) {
        document.getElementById(`option_${i}`).addEventListener("click", set_selected_task(`${i}`, document))
    }

};

function set_selected_task(target) {
    return () => {
        parses = document.getElementById("parses")
        var c = parses.children
        for (i = 0; i < c.length; i++){
            c[i].className = c[i].className.replace(/ selected/g, "");
        }

        document.getElementById(`option_${target}`).className += " selected";
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
    const meta = (document.getElementById("other_menu").value == "error_text") ? document.getElementById("other_response").value : "";
    return {
        task_id: task_id.value,
        answer: answer.value,
        meta: meta
    }
};
