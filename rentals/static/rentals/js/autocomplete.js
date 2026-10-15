
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("id_destination");
    const list = document.getElementById("location-suggestions");
    const status = document.getElementById("suggestion-status");

    if (!input || !list || !status) return;

    let timer;
    let controller;
    let activeIndex = -1;
    let suggestions = [];

    function closeSuggestions() {
        list.replaceChildren();
        list.hidden = true;
        suggestions = [];
        activeIndex = -1;
    }

    function selectSuggestion(location) {
        input.value = location.name;
        closeSuggestions();
        status.textContent = `Selected ${location.name}`;
        input.focus();
    }

    function renderSuggestions(results) {
        closeSuggestions();
        suggestions = results;

        if (!results.length) {
            status.textContent = "No matching destinations found.";
            return;
        }

        const fragment = document.createDocumentFragment();

        results.forEach((location, index) => {
            const option = document.createElement("button");
            option.type = "button";
            option.className = "suggestion-option";
            option.setAttribute("role", "option");
            option.setAttribute("aria-selected", "false");
            option.textContent = location.name;

            option.addEventListener("click", () => {
                selectSuggestion(location);
            });

            option.addEventListener("mouseenter", () => {
                setActive(index);
            });

            fragment.appendChild(option);
        });

        list.appendChild(fragment);
        list.hidden = false;
        status.textContent = `${results.length} suggestions available.`;
    }

    function setActive(index) {
        const options = list.querySelectorAll(".suggestion-option");
        if (!options.length) return;

        activeIndex = (index + options.length) % options.length;

        options.forEach((option, i) => {
            const active = i === activeIndex;
            option.classList.toggle("active", active);
            option.setAttribute("aria-selected", String(active));
        });
    }

    input.addEventListener("input", () => {
        clearTimeout(timer);

        if (controller) controller.abort();

        const query = input.value.trim();
        closeSuggestions();
        status.textContent = "";

        if (query.length < 2) return;

        timer = setTimeout(async () => {
            controller = new AbortController();

            try {
                const url = new URL(
                    "/api/locations/autocomplete/",
                    window.location.origin
                );
                url.searchParams.set("q", query);
                url.searchParams.set("limit", "8");

                const response = await fetch(url, {
                    signal: controller.signal,
                    headers: { Accept: "application/json" }
                });

                if (!response.ok) {
                    throw new Error("Autocomplete request failed");
                }

                const data = await response.json();

                // Ignore responses for text that has since changed.
                if (input.value.trim() !== query) return;

                renderSuggestions(data.results || []);
            } catch (error) {
                if (error.name !== "AbortError") {
                    status.textContent =
                        "Could not load suggestions. You can still submit your search.";
                }
            }
        }, 250);
    });

    input.addEventListener("keydown", (event) => {
        if (list.hidden) return;

        if (event.key === "ArrowDown") {
            event.preventDefault();
            setActive(activeIndex + 1);
        } else if (event.key === "ArrowUp") {
            event.preventDefault();
            setActive(activeIndex - 1);
        } else if (
            event.key === "Enter" &&
            activeIndex >= 0 &&
            suggestions[activeIndex]
        ) {
            event.preventDefault();
            selectSuggestion(suggestions[activeIndex]);
        } else if (event.key === "Escape") {
            closeSuggestions();
        }
    });

    document.addEventListener("click", (event) => {
        if (!event.target.closest(".destination-field")) {
            closeSuggestions();
        }
    });
});
