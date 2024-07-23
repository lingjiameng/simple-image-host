import re
import os
import uuid
import random

from pathlib import Path
from typing import Annotated, Union

from fastapi import Cookie, FastAPI, HTTPException, Header
from fastapi.responses import FileResponse

reg_b = re.compile(
    r"(android|bb\\d+|meego).+mobile|avantgo|bada\\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|mobile.+firefox|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\\.(browser|link)|vodafone|wap|windows ce|xda|xiino",
    re.I | re.M,
)

reg_v = re.compile(
    r"1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\\-(n|u)|c55\\/|capi|ccwa|cdm\\-|cell|chtm|cldc|cmd\\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\\-s|devi|dica|dmob|do(c|p)o|ds(12|\\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\\-|_)|g1 u|g560|gene|gf\\-5|g\\-mo|go(\\.w|od)|gr(ad|un)|haie|hcit|hd\\-(m|p|t)|hei\\-|hi(pt|ta)|hp( i|ip)|hs\\-c|ht(c(\\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\\-(20|go|ma)|i230|iac( |\\-|\\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\\/)|klon|kpt |kwc\\-|kyo(c|k)|le(no|xi)|lg( g|\\/(k|l|u)|50|54|\\-[a-w])|libw|lynx|m1\\-w|m3ga|m50\\/|ma(te|ui|xo)|mc(01|21|ca)|m\\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\\-2|po(ck|rt|se)|prox|psio|pt\\-g|qa\\-a|qc(07|12|21|32|60|\\-[2-7]|i\\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\\-|oo|p\\-)|sdk\\/|se(c(\\-|0|1)|47|mc|nd|ri)|sgh\\-|shar|sie(\\-|m)|sk\\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\\-|v\\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\\-|tdg\\-|tel(i|m)|tim\\-|t\\-mo|to(pl|sh)|ts(70|m\\-|m3|m5)|tx\\-9|up(\\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\\-|your|zeto|zte\\-",
    re.I | re.M,
)

CACHE_DATA = {}

IMAGE_LIB = "/"

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/img", response_class=FileResponse)
async def img_get(
    user_agent: Annotated[Union[str, None], Header()] = None,
    uid: Annotated[Union[str, None], Cookie()] = None,
):
    global CACHE_DATA
    lib = Path(IMAGE_LIB)
    if not lib.exists():
        raise HTTPException(status_code=500, detail=f"图片库目录{lib.absolute()}不存在")
    pc_lib = lib / "pc"
    if not pc_lib.exists():
        raise HTTPException(
            status_code=500, detail=f"PC图片库目录{pc_lib.absolute()}不存在"
        )
    mobile_lib = lib / "mobile"
    if not mobile_lib.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Mobile图片库目录{mobile_lib.absolute()}不存在",
        )
    print(uid)
    print(user_agent)
    # 生成uid
    if not uid:
        uid = str(uuid.uuid4())

    b = reg_b.search(user_agent)
    v = reg_v.search(user_agent[0:4])
    if b or v:
        img = random_img(mobile_lib, uid)
    else:
        img = random_img(pc_lib, uid)

    # 记录上次访问的url
    CACHE_DATA[uid] = img
    # 缓存过大直接清除缓存
    if len(CACHE_DATA) > 1000:
        CACHE_DATA = {}

    headers = {"Cache-Control": "no-cache,max-age=5"}
    rsp = FileResponse(img, headers=headers)
    rsp.set_cookie("uid", f"{uid}", samesite="none", secure=True)
    return rsp


def random_img(folder: Path, uid: str):
    global CACHE_DATA
    imgs = list(folder.iterdir())
    if len(imgs) == 0:
        raise HTTPException(
            status_code=500, detail=f"图片库目录{folder.absolute()}为空"
        )
    elif len(imgs) == 1:
        return imgs[0]
    else:
        if CACHE_DATA and uid and CACHE_DATA.get(uid, None):
            imgs.remove(CACHE_DATA.get(uid))
        return random.choice(imgs)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("SERVER_PORT", "8888"), 10)
    IMAGE_LIB = os.getenv("IMAGE_LIB", r"/app/image")
    uvicorn.run(app, host="0.0.0.0", port=port)
