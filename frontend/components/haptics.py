"""iPhone-style haptic feedback for the dashboard.

Browsers do not give web pages direct access to the iPhone's Taptic Engine, so three
layers are combined:

* Android (Chrome, Edge, Samsung Internet): the standard Vibration API, a short
  10 ms "tick" on every tap.
* iPhone / iPad on iOS 18+ (Safari and every other iOS browser): iOS plays its system
  haptic when a native ``<input type="checkbox" switch>`` is toggled, so a hidden
  switch is toggled on each tap.  On older iOS versions nothing happens.
* Every device (and laptops, which cannot vibrate): an iOS-style "spring" press
  animation, where controls shrink slightly while pressed and bounce back.

The script is installed once into the page (not into Streamlit's component iframe),
so it keeps working across reruns; ``set_enabled`` just flips a flag.
"""
import json

import streamlit as st
import streamlit.components.v1 as components

# Things that should "tick" when tapped.
_TARGETS = ", ".join([
    "button", "a[href]", "[role='tab']", "[role='radio']", "[role='switch']",
    "[role='option']", "[data-baseweb='select']", "[data-baseweb='checkbox']",
    "[data-testid='stExpander'] summary", "[data-testid='stFileUploaderDropzone']",
    ".js-plotly-plot",
])

_PAGE_SCRIPT = r"""
(function () {
  if (window.__cdiHapticsInstalled) return;
  window.__cdiHapticsInstalled = true;
  if (window.__cdiHapticsOn === undefined) window.__cdiHapticsOn = true;

  var TARGETS = %s;

  // Hidden native switch: toggling it makes iOS 18+ play its system haptic.
  var label = document.createElement('label');
  label.setAttribute('aria-hidden', 'true');
  label.id = 'cdi-haptic-switch';
  label.style.cssText = 'position:fixed;left:-200px;top:0;width:1px;height:1px;opacity:0;overflow:hidden;pointer-events:none';
  var input = document.createElement('input');
  input.type = 'checkbox';
  input.setAttribute('switch', '');
  input.tabIndex = -1;
  label.appendChild(input);
  document.body.appendChild(label);

  var canVibrate = typeof navigator.vibrate === 'function';
  var isApple = /iPhone|iPad|iPod/.test(navigator.userAgent) ||
                (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  var last = 0;

  window.cdiHaptic = function (ms) {
    if (!window.__cdiHapticsOn) return;
    var now = Date.now();
    if (now - last < 40) return;               // one tick per tap, not per bubbling event
    last = now;
    if (canVibrate) {
      try { navigator.vibrate(ms || 10); } catch (e) {}
    } else if (isApple) {
      label.click();                           // must run inside the tap itself
    }
  };

  // capture phase, so the tick happens before Streamlit starts its rerun
  document.addEventListener('click', function (ev) {
    var t = ev.target;
    if (!t || !t.closest || t.closest('#cdi-haptic-switch')) return;
    var hit = t.closest(TARGETS);
    if (!hit || hit.disabled || hit.getAttribute('aria-disabled') === 'true') return;
    window.cdiHaptic(hit.matches('[kind="primary"], [class*="st-key-run_btn"] button') ? 18 : 10);
  }, true);
})();
"""

# iOS-style press: shrink a little while held, spring back on release.
_PRESS_CSS = """
<style>
:root{--cdi-spring:cubic-bezier(.34,1.56,.64,1)}
.stButton button,.stDownloadButton button,[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-primary"],[role="tab"],[data-baseweb="select"]>div,
div[data-testid="stRadio"] label,.kpi,.row,.insight{
  transition:transform .32s var(--cdi-spring),filter .2s ease!important}
.stButton button:active,.stDownloadButton button:active,[role="tab"]:active,
div[data-testid="stRadio"] label:active,[data-baseweb="select"]>div:active{
  transform:scale(.95)!important;filter:brightness(1.12);transition-duration:.08s!important}
.kpi:active,.row:active,.insight:active{transform:scale(.98)!important;transition-duration:.08s!important}
/* the pipeline stepper: the invisible button is pressed, the ring reacts */
[class*="st-key-stage_row"] [data-testid="stColumn"]:active .pf-ring,
[class*="st-key-stage_row"] [data-testid="column"]:active .pf-ring{
  transform:scale(.88)!important;transition:transform .08s ease!important}
@media (prefers-reduced-motion:reduce){
  .stButton button:active,.kpi:active,.row:active,.insight:active{transform:none!important}}
</style>
"""


def enable_haptics(enabled=True):
    """Install haptics + press animation (once) and switch them on or off."""
    if enabled:
        st.markdown(_PRESS_CSS, unsafe_allow_html=True)
    script = _PAGE_SCRIPT % json.dumps(_TARGETS)
    # Runs in a tiny component iframe, then injects the real script into the
    # dashboard page itself so it survives reruns.
    installer = (
        "<script>(function(){var w=window.parent;"
        f"w.__cdiHapticsOn={json.dumps(bool(enabled))};"
        "if(w.__cdiHapticsInstalled)return;"
        "var s=w.document.createElement('script');"
        f"s.textContent={json.dumps(script)};"
        "w.document.head.appendChild(s);})();</script>"
    )
    if hasattr(st, "iframe"):                 # newer Streamlit: components.html is deprecated
        st.iframe(installer, height=1)
    else:
        components.html(installer, height=0)