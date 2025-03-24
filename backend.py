from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
from datetime import datetime, timedelta

app = FastAPI()

# 跨域设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据库配置
db_config = {
    'host': '111.119.242.63',
    'port': 3306,
    'user': 'zhukeyun',
    'password': 'yytt0324',
    'database': 'media_corpus'
}

# 获取新闻
@app.get("/news")
def get_news(
        search: str = "",
        page: int = 1,
        page_size: int = 10,
        time_start: str = None,
        time_end: str = None,
        sort_by: str = "ctime",
        sort_order: str = "desc"
):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    offset = (page - 1) * page_size
    today_start = int(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
    today_end = int(datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999).timestamp())
    exclude_tags = "'A股盘面直播', '港股动态', '美股动态', 'A股公告速递', '期货市场情报', '股指期货', '券商动态', '禽畜期货', '能源类期货', '黄金'"

    # 默认条件：当天数据
    conditions = [f"n.ctime BETWEEN %s AND %s AND (s.subject_name IS NULL OR s.subject_name NOT IN ({exclude_tags}))"]
    params = [today_start, today_end]

    if search:
        conditions.append("(n.content LIKE %s OR s.subject_name LIKE %s)")
        params.extend([f"%{search}%", f"%{search}%"])
    if time_start:
        conditions.append("n.ctime >= %s")
        start_timestamp = int(datetime.strptime(time_start, "%Y-%m-%d").timestamp())
        params.append(start_timestamp)
    if time_end:
        conditions.append("n.ctime <= %s")
        end_timestamp = int(datetime.strptime(time_end, "%Y-%m-%d").replace(hour=23, minute=59, second=59).timestamp())
        params.append(end_timestamp)

    where_clause = " WHERE " + " AND ".join(conditions)
    sort_column = {"ctime": "n.ctime", "hotspot_level": "n.hotspot_level"}.get(sort_by, "n.ctime")
    sort_direction = "DESC" if sort_order == "desc" else "ASC"

    count_query = f"SELECT COUNT(DISTINCT n.id) as total FROM perception_cls_news n LEFT JOIN perception_cls_news_subjects s ON n.id = s.news_id {where_clause}"
    cursor.execute(count_query, params)
    total = cursor.fetchone()["total"]

    query = f"""
        SELECT n.id, n.ctime, n.content, n.hotspot_level, n.feature_scores, GROUP_CONCAT(s.subject_name) as subject_name
        FROM perception_cls_news n
        LEFT JOIN perception_cls_news_subjects s ON n.id = s.news_id
        {where_clause}
        GROUP BY n.id
        ORDER BY {sort_column} {sort_direction}
        LIMIT %s OFFSET %s
    """
    params.extend([page_size, offset])
    cursor.execute(query, params)
    results = cursor.fetchall()
    try:
        conn.close()
    except:
        pass
    return {"data": results, "total": total}

# 获取事件列表
@app.get("/events")
def get_events(
        search: str = "",
        page: int = 1,
        page_size: int = 10,
        time_start: str = None,
        time_end: str = None,
        hotspot_levels: str = None,
        sort_by: str = "expected_time",
        sort_order: str = "asc"
):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    offset = (page - 1) * page_size
    today = datetime.now().date()

    # 基本条件：只返回 is_important = 1 的事件
    conditions = ["e.is_important = 1", "e.expected_time >= %s"]
    params = [today]

    if search:
        conditions.append("e.event_description LIKE %s")
        params.append(f"%{search}%")
    if time_start:
        conditions.append("e.expected_time >= %s")
        params.append(time_start)
    if time_end:
        conditions.append("e.expected_time <= %s")
        params.append(time_end)
    if hotspot_levels:
        levels = hotspot_levels.split(",")
        conditions.append("n.hotspot_level IN ({})".format(",".join(["%s"] * len(levels))))
        params.extend(levels)

    where_clause = " WHERE " + " AND ".join(conditions)
    sort_column = {
        "expected_time": "e.expected_time",
        "hotspot_level": "n.hotspot_level",
        "probability": "e.probability_of_occurrence"
    }.get(sort_by, "e.expected_time")
    sort_direction = "DESC" if sort_order == "desc" else "ASC"

    # 总数查询
    count_query = f"SELECT COUNT(*) as total FROM perception_future_events e LEFT JOIN perception_cls_news n ON e.news_id = n.id {where_clause}"
    print(f"Count Query: {count_query % tuple(params)}")  # 调试输出
    cursor.execute(count_query, params)
    total = cursor.fetchone()["total"]

    # 数据查询
    query = f"""
        SELECT e.id, e.news_id, e.event_description, e.expected_time, e.remarks, e.created_at, 
               e.probability_of_occurrence, e.theme_categories, e.region_categories, n.content, n.hotspot_level
        FROM perception_future_events e
        LEFT JOIN perception_cls_news n ON e.news_id = n.id
        {where_clause}
        ORDER BY {sort_column} {sort_direction}, n.hotspot_level DESC
        LIMIT %s OFFSET %s
    """
    params.extend([page_size, offset])
    print(f"Select Query: {query % tuple(params)}")  # 调试输出
    cursor.execute(query, params)
    results = cursor.fetchall()

    conn.close()
    return {"data": results, "total": total}


# 删除事件（标记为不重要）
@app.post("/events/delete/{event_id}")
def delete_event(event_id: int):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    current_timestamp = int(datetime.now().timestamp())

    # 更新语句：仅需将 is_important 设为 0，不强制要求原值为 1
    query = """
        UPDATE perception_future_events 
        SET is_important = 0, updated_at = %s 
        WHERE id = %s
    """
    params = (current_timestamp, event_id)  # 元组格式
    print(f"Delete Query: {query % params}")  # 调试输出

    try:
        cursor.execute(query, params)
        conn.commit()
        affected_rows = cursor.rowcount
        print(f"Event ID: {event_id}, Updated rows: {affected_rows}")

        if affected_rows == 0:
            raise HTTPException(status_code=404, detail=f"Event with id {event_id} not found")

        return {"message": "Event marked as unimportant successfully"}
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)