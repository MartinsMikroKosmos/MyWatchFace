"""Builds watchface.xml for the Aurora watch face.

Usage:  python3 tools/watchface/gen_xml.py

The static layout lives in aurora_base.xml; this script replaces its placeholder rings with
complication slots (steps, activity, distance) that default to the Fitbit data sources.
Bitmaps come from gen_assets.py (needs pillow + numpy).

Note: the watch stores the chosen data sources per slot position, so after adding, removing or
reordering slots the app has to be reinstalled (uninstall first) for the defaults to line up.
"""
import os
import re
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "../../watchface/src/main/res/raw/watchface.xml")

FONT = 'family="SYNC_TO_DEVICE"'
HIDE_IN_AMBIENT = '<Variant mode="AMBIENT" target="alpha" value="0" />'

FITBIT = "com.fitbit.FitbitMobile/com.fitbit.complications."
STEPS = FITBIT + "offloadable.steps.OffloadableStepsComplicationDataSourceService"
AZM = FITBIT + "azm.AZMComplicationDataSourceService"
DISTANCE = FITBIT + "distance.DistanceComplicationDataSourceService"

STEP_GOAL = "([STEP_GOAL] &gt;= 1000 ? [STEP_GOAL] : 10000)"
RANGED_PROGRESS = ("clamp(([COMPLICATION.RANGED_VALUE_VALUE] - [COMPLICATION.RANGED_VALUE_MIN]) / "
                   "([COMPLICATION.RANGED_VALUE_MAX] - [COMPLICATION.RANGED_VALUE_MIN]), 0, 1)")
GOAL_PROGRESS = "clamp([COMPLICATION.GOAL_PROGRESS_VALUE] / [COMPLICATION.GOAL_PROGRESS_TARGET_VALUE], 0, 1)"
PROGRESS = {"RANGED_VALUE": RANGED_PROGRESS, "GOAL_PROGRESS": GOAL_PROGRESS}
TYPES = ["RANGED_VALUE", "GOAL_PROGRESS", "SHORT_TEXT", "EMPTY"]

# Rough distance from steps (75 cm stride), shown while the distance slot has no data source.
DISTANCE_ESTIMATE = 'numberFormat(&quot;0.0&quot;, [STEP_COUNT] * 0.00075)'


def indent(block, n):
    return "\n" + textwrap.indent(textwrap.dedent(block).strip("\n"), " " * n)


def text(x, y, w, h, content, size, color="#ffffffff", weight="NORMAL", ellipsis=False):
    ell = ' ellipsis="TRUE"' if ellipsis else ""
    return f"""
<PartText height="{h}" width="{w}" x="{x}" y="{y}">
    <Text align="CENTER"{ell}>
        <Font color="{color}" {FONT} size="{size}" weight="{weight}">{content}</Font>
    </Text>
</PartText>"""


def tmpl(fmt, *exprs):
    params = "".join(f'<Parameter expression="{e}" />' for e in exprs)
    return f"<Template>{fmt}{params}</Template>"


def image(x, y, w, h, res):
    return f"""
<PartImage height="{h}" width="{w}" x="{x}" y="{y}">
    <Image resource="{res}" />
</PartImage>"""


def arc(color, progress=None):
    """Ring arc in the 96x88 ring box, open at the bottom."""
    tr = f'\n    <Transform target="endAngle" value="-125 + 250 * {progress}" />' if progress else ""
    return f"""
<Arc centerX="48" centerY="44" endAngle="125" height="80" startAngle="-125" width="80">{tr}
    <Stroke cap="ROUND" color="{color}" thickness="7" />
</Arc>"""


def ring(t, color, icon, value, subtitle, progress):
    """One ring: dim track, optional progress arc, icon, value and a second line."""
    dim = "#33" + color[3:]
    arcs = arc(dim) + arc(color, progress) if progress else arc(color)
    return (f"""
<PartDraw height="88" width="96" x="0" y="0">{indent(arcs, 4)}
</PartDraw>""" + image(39, 10, 18, 18, icon)
            + text(8, 26, 80, 28, value, 22, weight="SEMI_BOLD", ellipsis=True)
            + text(13, 52, 70, 18, subtitle, 14, color, "MEDIUM", ellipsis=True))


def empty_ring(color):
    return f"""
<PartDraw height="88" width="96" x="0" y="0">{indent(arc("#33" + color[3:]), 4)}
</PartDraw>""" + image(37, 33, 22, 22, "ic_plus")


def goal_line(t, unit):
    if t == "GOAL_PROGRESS":
        return tmpl(f"/ %d {unit}", "[COMPLICATION.GOAL_PROGRESS_TARGET_VALUE]")
    if t == "RANGED_VALUE":
        return tmpl(f"/ %d {unit}", "[COMPLICATION.RANGED_VALUE_MAX]")
    return tmpl("%s", "[COMPLICATION.TITLE]")


def steps(t):
    color = "#ff34d17a"
    if t == "EMPTY":  # no data source: the watch's own step count
        return ring(t, color, "ic_steps", tmpl("%s", 'numberFormat(&quot;#,###&quot;, [STEP_COUNT])'),
                    tmpl("/ %dK", f"round({STEP_GOAL} / 1000)"), f"clamp([STEP_COUNT] / {STEP_GOAL}, 0, 1)")
    target = {"GOAL_PROGRESS": "[COMPLICATION.GOAL_PROGRESS_TARGET_VALUE]",
              "RANGED_VALUE": "[COMPLICATION.RANGED_VALUE_MAX]"}.get(t)
    sub = tmpl("/ %dK", f"round({target} / 1000)") if target else tmpl("%s", "[COMPLICATION.TITLE]")
    return ring(t, color, "ic_steps", tmpl("%s", "[COMPLICATION.TEXT]"), sub, PROGRESS.get(t))


def activity(t):
    color = "#ffff8a3d"
    if t == "EMPTY":
        return empty_ring(color)
    return ring(t, color, "ic_activity", tmpl("%s", "[COMPLICATION.TEXT]"), goal_line(t, "Min."), PROGRESS.get(t))


def distance(t):
    color = "#ff4f8dff"
    if t == "EMPTY":
        return ring(t, color, "ic_pin", tmpl("%s", DISTANCE_ESTIMATE), "km", None)
    return ring(t, color, "ic_pin", tmpl("%s", "[COMPLICATION.TEXT]"), "km", PROGRESS.get(t))


def slot(slot_id, name, x, render, provider, provider_type):
    comps = "".join(f'\n    <Complication type="{t}">{indent(render(t), 8)}\n    </Complication>' for t in TYPES)
    return f"""
<ComplicationSlot
    slotId="{slot_id}"
    displayName="{name}"
    height="88"
    width="96"
    x="{x}"
    y="282"
    supportedTypes="{' '.join(TYPES)}">
    <DefaultProviderPolicy defaultSystemProvider="EMPTY" defaultSystemProviderType="EMPTY" primaryProvider="{provider}" primaryProviderType="{provider_type}" secondaryProvider="{provider}" secondaryProviderType="SHORT_TEXT" />
    {HIDE_IN_AMBIENT}
    <BoundingOval height="88" width="88" x="4" y="0" />{comps}
</ComplicationSlot>"""


src = open(os.path.join(HERE, "aurora_base.xml")).read()
body = src[src.index("<!-- ============ Background"):src.index("<!-- ============ Ambient")]
body = re.sub(r"\s*<ComplicationSlot.*?</ComplicationSlot>", "", body, flags=re.S)
# The base file's native steps ring becomes a slot; only its label stays static.
steps_label = text(82, 364, 96, 22, "Schritte", 16, "#ffb0b4c4").replace(
    "<PartText ", '<PartText name="stepsLabel" ', 1).replace('">', '">\n    ' + HIDE_IN_AMBIENT, 1)
body = re.sub(r"<!-- =+ Ring 1: steps.*?</Group>",
              "<!-- ============ Ring 1: steps (label; value is complication slot 0) ============ -->"
              + indent(steps_label, 8), body, flags=re.S)
body = body.replace("Ring 2: activity (complication)", "Ring 2: activity (label; complication slot 1)")
body = body.replace("Ring 3: distance (complication)", "Ring 3: distance (label; complication slot 2)")
ambient = src[src.index("        <!-- ============ Ambient"):src.index("    </Scene>")]

slots = (slot(0, "steps_slot", 82, steps, STEPS, "GOAL_PROGRESS")
         + slot(1, "activity_slot", 177, activity, AZM, "GOAL_PROGRESS")
         + slot(2, "distance_slot", 272, distance, DISTANCE, "SHORT_TEXT"))

xml = f"""<?xml version="1.0" encoding="utf-8"?>
<WatchFace
    height="450"
    width="450">
    <Metadata
        key="CLOCK_TYPE"
        value="DIGITAL" />
    <Scene backgroundColor="#ff000000">
        {body.strip()}
        <!-- ============ Complication slots: steps, activity, distance (Fitbit by default) ============ -->{indent(slots, 8)}
{ambient.rstrip()}
    </Scene>
</WatchFace>
"""
xml = re.sub(r"\n\s*\n", "\n", xml)
open(PATH, "w").write(xml)
print("written", len(xml.splitlines()), "lines")
