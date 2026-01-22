import streamlit as st
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates

W, H = 1100, 650

#time period for input burstiness filter
BURST_SAME = 260


BG = (20, 22, 26)

DONE = (210, 60, 60)   # red
WORK = (70, 190, 120)  # green


def init_state():
    if "history" not in st.session_state:
        st.session_state.history = [{"polys": [], "working": []}]
        st.session_state.hist_i = 0




    if "last_seen_ut" not in st.session_state:
        st.session_state.last_seen_ut = None

    if "last_accept_ut" not in st.session_state:
        st.session_state.last_accept_ut = None
        st.session_state.last_accept_xy = None


def cur():
    return st.session_state.history[st.session_state.hist_i]


def push(state):
    if st.session_state.hist_i < len(st.session_state.history) - 1:                             #redo filter
        st.session_state.history = st.session_state.history[: st.session_state.hist_i + 1]
    st.session_state.history.append(state)
    st.session_state.hist_i += 1


def reset_click_filters():
    st.session_state.last_seen_ut = None
    st.session_state.last_accept_ut = None
    st.session_state.last_accept_xy = None


def render(state):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    for poly in state["polys"]:
        if len(poly) >= 2:
            pts = [tuple(p) for p in poly]
            d.line(pts + [pts[0]], fill=DONE, width=2)
        for x, y in poly:
            d.ellipse((x - 4, y - 4, x + 4, y + 4), fill=DONE)



    w = state["working"]
    if w:
        pts = [tuple(p) for p in w]
        if len(w) >= 2:
            d.line(pts, fill=WORK, width=2)

        for i, (x, y) in enumerate(w):
            r = 6 if i == 0 else 4
            d.ellipse((x - r, y - r, x + r, y + r), fill=WORK)

    return img


def accept_click(x, y, ut_ms):

    if ut_ms is None:
        return False



    if st.session_state.last_seen_ut == ut_ms:
        return False

    st.session_state.last_seen_ut = ut_ms

    last_ut = st.session_state.last_accept_ut
    last_xy = st.session_state.last_accept_xy

    if last_ut is not None and last_xy is not None:
        if (x, y) == last_xy and (ut_ms - last_ut) < BURST_SAME:
            return False




    st.session_state.last_accept_ut = ut_ms
    st.session_state.last_accept_xy = (x, y)
    return True


def add_point(x, y):
    state = cur()
    polys = [p[:] for p in state["polys"]]
    working = [p[:] for p in state["working"]]
    working.append([int(x), int(y)])
    push({"polys": polys, "working": working})




def close_polygon():
    state = cur()


    polys = [p[:] for p in state["polys"]]
    working = [p[:] for p in state["working"]]

    if len(working) >= 3:
        polys.append(working)
        push({"polys": polys, "working": []})
        reset_click_filters()


st.set_page_config(page_title="Polygon Pro", layout="wide")
init_state()

c1, c2, c3, _ = st.columns([1, 1, 2, 6])
if c1.button("Undo"):
    if st.session_state.hist_i > 0:
        st.session_state.hist_i -= 1
        reset_click_filters()
        st.rerun()

if c2.button("Redo"):
    if st.session_state.hist_i < len(st.session_state.history) - 1:
        st.session_state.hist_i += 1
        reset_click_filters()
        st.rerun()



can_close = len(cur()["working"]) >= 3
if c3.button("Close polygon", disabled=not can_close):
    close_polygon()
    st.rerun()

img = render(cur())
click = streamlit_image_coordinates(img, key="board")


if (
    click is not None
    and isinstance(click, dict)
    and click.get("x") is not None
    and click.get("y") is not None
):
    x = int(click["x"])
    y = int(click["y"])
    ut = click.get("unix_time")
    ut = int(ut) if ut is not None else None

    if accept_click(x, y, ut):
        add_point(x, y)
        st.rerun()
