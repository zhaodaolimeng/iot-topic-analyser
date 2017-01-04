# iot-topic-analyser

一个用于分析xively.com物联网平台上设备功能的小工具  

# 输入数据结构

包括每个传感器所属应用的信息feed_t以及每个传感器自身信息datasteam_t

```
create table feed_t (
    id bigint(20),
    created datetime,
    creator varchar(255),
    description text,
    device_name varchar(255),
    disposition varchar(255),
    domain varchar(255),
    ele varchar(255),
    exposure varchar(255),
    feedUrl varchar(255),
    icon varchar(255),
    isalive bit(1),
    lat varchar(255),
    lng varchar(255),
    private bit(1),
    status varchar(255),
    tags varchar(255),
    title varchar(255),
    updated datetime,
    user_login varchar(255),
    version varchar(255),
    website varchar(255)
); 
create table datastream_t(
    id bigint(20),
    current_value varchar(255),
    feedid bigint(20),
    max_value varchar(255),
    min_value varchar(255),
    streamid varchar(255),
    tags varchar(255),
    unit_symbol varchar(255),
    unit_type varchar(255),
    units varchar(255),
    updated datetime,
    label varchar(255)
);
create table datapoint_t(
    feedid bigint(20),
    streamid varchar(255),
    time_at datetime,
    value varchar(255)
);
```

