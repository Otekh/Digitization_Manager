/* OTEKH Digitization Manager - client behaviour.
   Vanilla JS only: user menu, theme/sub-theme rows, date format toggle,
   summary character counter. */

(function () {
  "use strict";

  // ---- user menu dropdown ----
  var menu = document.getElementById("usermenu");
  if (menu) {
    var btn = menu.querySelector(".usermenu-btn");
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      menu.classList.toggle("open");
      btn.setAttribute("aria-expanded", menu.classList.contains("open"));
    });
    document.addEventListener("click", function () {
      menu.classList.remove("open");
      btn.setAttribute("aria-expanded", "false");
    });
  }

  // ---- theme -> sub-theme filtering + add/remove rows ----
  var subData = {};
  var dataEl = document.getElementById("subthemes-data");
  if (dataEl) {
    try { subData = JSON.parse(dataEl.textContent); } catch (e) { subData = {}; }
  }

  function fillSubs(subSelect, theme) {
    subSelect.innerHTML = "";
    var empty = document.createElement("option");
    empty.value = "";
    empty.textContent = "-- sub theme --";
    subSelect.appendChild(empty);
    (subData[theme] || []).forEach(function (s) {
      var o = document.createElement("option");
      o.value = s;
      o.textContent = s;
      subSelect.appendChild(o);
    });
    var unk = document.createElement("option");
    unk.value = "Unknown";
    unk.textContent = "Unknown";
    subSelect.appendChild(unk);
  }

  var rowsWrap = document.getElementById("subject-rows");
  if (rowsWrap) {
    rowsWrap.addEventListener("change", function (e) {
      if (e.target.classList.contains("theme-select")) {
        var row = e.target.closest(".subject-row");
        fillSubs(row.querySelector(".sub-select"), e.target.value);
      }
    });
    rowsWrap.addEventListener("click", function (e) {
      if (e.target.classList.contains("subject-remove")) {
        var rows = rowsWrap.querySelectorAll(".subject-row");
        if (rows.length > 1) {
          e.target.closest(".subject-row").remove();
        }
      }
    });
    var addBtn = document.getElementById("subject-add");
    if (addBtn) {
      addBtn.addEventListener("click", function () {
        var clone = rowsWrap.querySelector(".subject-row").cloneNode(true);
        clone.querySelector(".theme-select").value = "";
        fillSubs(clone.querySelector(".sub-select"), "");
        rowsWrap.appendChild(clone);
      });
    }
  }

  // ---- date format toggle ----
  var fmt = document.getElementById("date_format");
  var dateInput = document.getElementById("date_value");
  if (fmt && dateInput) {
    var placeholders = {
      year: "YYYY",
      month_year: "MM/YYYY",
      full: "DD/MM/YYYY",
      unknown: "Unknown"
    };
    function syncDate() {
      if (fmt.value === "unknown") {
        dateInput.value = "Unknown";
        dateInput.disabled = true;
      } else {
        dateInput.disabled = false;
        if (dateInput.value === "Unknown") dateInput.value = "";
        dateInput.placeholder = placeholders[fmt.value] || "Select a format first";
      }
    }
    fmt.addEventListener("change", syncDate);
    syncDate();
  }

  // ---- flag toggles: show the per-field reason input when switched on ----
  var flagBoxes = document.querySelectorAll("input[name='flag']");
  flagBoxes.forEach(function (box) {
    var reason = document.querySelector(
      "input[name='flag_reason_" + box.value + "']"
    );
    function syncFlag() {
      if (reason) {
        reason.hidden = !box.checked;
        reason.required = box.checked;
        if (box.checked) reason.focus();
      }
    }
    box.addEventListener("change", syncFlag);
    syncFlag();
  });

  // ---- expert review: any flag on -> Return to User, else Finalize ----
  var btnFinalize = document.getElementById("btn-finalize");
  var btnReturn = document.getElementById("btn-return");
  if (flagBoxes.length && btnFinalize && btnReturn) {
    function syncFlagButtons() {
      var any = Array.prototype.some.call(flagBoxes, function (b) {
        return b.checked;
      });
      btnFinalize.hidden = any;
      btnReturn.hidden = !any;
    }
    flagBoxes.forEach(function (b) {
      b.addEventListener("change", syncFlagButtons);
    });
    syncFlagButtons();
  }

  // ---- summary counter ----
  var summary = document.getElementById("summary");
  var counter = document.getElementById("summary-count");
  if (summary && counter) {
    function syncCount() {
      counter.textContent = summary.value.length;
      counter.style.color = summary.value.length < 50 ? "#8a3535" : "";
    }
    summary.addEventListener("input", syncCount);
    syncCount();
  }
})();
