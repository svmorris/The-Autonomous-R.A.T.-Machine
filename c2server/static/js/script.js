const toggle_details = (target_id) => {
    // toggle rotating the button
    const toggle_button = document.getElementById(`toggle_button_${target_id}`);
    if (toggle_button.classList.contains("rotate")) {
        toggle_button.classList.remove("rotate");
        toggle_button.classList.add("unrotate");
    } else {
        toggle_button.classList.remove("unrotate");
        toggle_button.classList.add("rotate");
    }

    // toggle collapsing the details
    const element = document.getElementById(`details_${target_id}`);
    if (element.classList.contains('collapsed')) {
        element.classList.remove('collapsed');
        element.style.height = 'auto';
        let height = element.scrollHeight + 'px';
        element.style.padding = '25px';
        element.style.height = '0px';

        setTimeout(() => {
            element.style.height = height;
        }, 0);
        localStorage.setItem(`isCollapsed_${target_id}`, 'false');
    } else {
        element.style.height = `${element.scrollHeight}px`;
        element.offsetHeight;
        element.style.height = '0px';
        element.classList.add('collapsed');
        localStorage.setItem(`isCollapsed_${target_id}`, 'true');
    }
}


const toggle_pause_target = (instance, target_id) => {
    fetch(`/api/v0/pause/${instance}/${target_id}`, {
        method: "GET",
    })
    .then(response => response.json())
    .then(_ => {
        const pause_button = document.getElementById(`pause_button_${target_id}`);
        if (pause_button.innerText === "pause")
            pause_button.innerText = "resume";
        else
            pause_button.innerText = "pause";

    })
    .catch(error => console.error('Error:', error));
}

const set_stored_target_details_state = (target_id) => {
    const isCollapsed = localStorage.getItem(`isCollapsed_${target_id}`);
    const element = document.getElementById(`details_${target_id}`);
    const toggle_button = document.getElementById(`toggle_button_${target_id}`);

    if (isCollapsed === 'true') {
        toggle_button.classList.remove("rotate");
        toggle_button.classList.add("unrotate");
        element.classList.add('collapsed');
        element.style.height = '0';
        element.style.padding = '0';
        element.style.margin = '0';
    } else if (isCollapsed === 'false') {
        toggle_button.classList.remove("unrotate");
        toggle_button.classList.add("rotate");
        element.classList.remove('collapsed');
        element.style.height = 'auto';
        element.style.padding = '25px';
        // Optionally, set specific height, padding, and margin if needed
    }
};




const get_report = (instance, target_id) => {
    const report_button = document.getElementById(`report_button_${target_id}`)
    report_button.disabled=true;
    report_button.innerText = "generating report...";


    fetch(`/api/v0/report/${instance}/${target_id}`, {
        method: "GET",
    })
    .then(response => response.json())
    .then(_ => {
        document.location.reload();
    })
    .catch(error => console.error('Error:', error))

}
