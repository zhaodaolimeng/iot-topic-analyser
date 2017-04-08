/*
 * curiosity_20161204的翻译不全
 * 将curiosity_v3的描述和curiosity_20161204的数据进行拼接
 * */
use curiosity_20161226;

-- drop table if exists features_t;
create table features_t (
	feedid bigint(20),
	streamid varchar(255),
	doc text,
	iana varchar(20),
	location_type varchar(50),
	created date
);
create table label_mapping_t(
	origin_label varchar(255),
	level1_label varchar(255),
	level2_label varchar(255)
);
insert into label_mapping_t (origin_label) select label from manual_label_t group by label;


select count(*) as sensor_cnt, floor(T.cnt/100) as point_cnt from (
	select feedid, datastreamid, count(*) as cnt 
	from datapoint_t group by feedid, datastreamid
)as T group by floor(T.cnt/100);

select T.feedid, T.datastreamid from (
	select feedid, datastreamid, count(*) as cnt 
	from datapoint_t group by feedid, datastreamid
)as T; 	

select floor(length(description)/200) as len, count(*) as cnt from feed_t group by floor(length(description)/200);

desc feed_t;
desc datastream_t;

