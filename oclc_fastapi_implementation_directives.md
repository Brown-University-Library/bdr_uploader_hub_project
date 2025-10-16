Four things:
- review the `pyproject.toml' "llm_code_directives"
- review "bdr_uploader_hub_project/oclc_fastapi_implementation_directives.md"
- an htmx requirement
- _possibly_ useful code
- plan document

---

the htmx requirement -- more info

In the student-form django template, if the form will display the keyword field, I'd like to add an htmx feature that calls the url "check_oclc_fastapi" endpoint with text as the user types. The endpoint will return authority-keyword suggestions that the user should be able to choose, or ignore.

But one additional feature...

I want the single form-field to be able to capture multiple keywords, separated by pipes. Example: the user should be able to enter:

economic development | world bank

...and on submission, the processing code would turn that single string into two keywords.

This means that the htmx code would need to be able to "reset" the string being sent to the auto-suggester url endpoint after a pipe-character. Can htmx handle this?

---

the _possibly_ useful code -- more info

An LLM previously offered these suggestions, not knowing about the above pipe-requires-resetting-text-for-auto-suggester feature:

```
1) Debounced “search-as-you-type” + cancels stale requests
Template (Django)
<!-- templates/authorities/form.html -->
<label for="id_authority">Authority term</label>
<input
  id="id_authority"
  name="q"
  type="search"
  autocomplete="off"
  spellcheck="false"
  placeholder="Begin typing…"
  hx-get="{% url 'suggest_authority_terms' %}"
  hx-trigger="input changed delay:250ms, keyup[key=='Enter']"
  hx-target="#authority-suggestions"
  hx-sync="this:replace"
  hx-indicator=".authority-spinner"
  aria-controls="authority-suggestions"
  aria-autocomplete="list"
  role="combobox"
/>

<span class="authority-spinner" aria-hidden="true" style="display:inline-block">
  <!-- htmx will toggle the .htmx-request class on this element -->
  <svg width="16" height="16" viewBox="0 0 50 50" class="spinner">
    <circle cx="25" cy="25" r="20" stroke-width="5" fill="none"></circle>
  </svg>
</span>

<ul id="authority-suggestions" role="listbox" class="suggestions"></ul>


delay:250ms debounces keystrokes; changed ignores non-changes (e.g., arrow keys).

hx-sync="this:replace" aborts any in-flight request and uses only the latest—critical for fast typers. 
htmx.org
+1

hx-indicator adds/removes htmx-request on the spinner so you can style “loading.” 
htmx.org

Minimal CSS (optional):

.authority-spinner { opacity: 0; transition: opacity .15s; }
.authority-spinner.htmx-request { opacity: 1; }

URLconf
# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("authorities/suggest/", views.suggest_authority_terms, name="suggest_authority_terms"),
]

View
# views.py
from typing import Any
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

def suggest_authority_terms(request: HttpRequest) -> HttpResponse:
    """
    Return an HTML <li> list of suggested authority terms for q.
    """
    q: str = (request.GET.get("q") or "").strip()
    results: list[str] = [] if len(q) < 2 else lookup_authority_terms(q)  # your lookup
    return render(request, "authorities/_suggestions.html", {"results": results, "q": q})

def lookup_authority_terms(q: str) -> list[str]:
    """
    Perform lookup for authority terms matching q.
    """
    # Replace with your real search (Solr/DB/API):
    sample: list[str] = ["Apple", "Appalachia", "Application security", "Applied physics"]
    ql = q.lower()
    return [s for s in sample if ql in s.lower()][:10]

Partial template (response)
<!-- templates/authorities/_suggestions.html -->
{% if results %}
  {% for item in results %}
    <li role="option">
      <button type="button"
              hx-get="#"
              hx-on:click="document.querySelector('#id_authority').value='{{ item|escapejs }}'">
        {{ item }}
      </button>
    </li>
  {% endfor %}
{% else %}
  <li role="option" aria-disabled="true">No suggestions</li>
{% endif %}


Docs: hx-trigger modifiers delay, changed, and throttle; example “Active Search”; and hx-sync strategies. 
htmx.org
```

Offer me your own suggestion -- it doesn't have to incorporate the above code-suggestions.

---

(3) Make a plan

Don't write any code yet -- rather, make a plan about what files will be updated, and how. Provide enough context so that if we proceed in a different session, you have enough context to proceed. Save the plan to "bdr_uploader_hub_project/oclc_fastapi_implementation_plan.md".

---
