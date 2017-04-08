/**
 * 该脚本用于生成：
 * 1. 手工标记sensor序列datastream_label_t
 * 2. 机器翻译的文本数据
 */

create database curiosity_20161207;
use curiosity_20161207;

-- 合并feed_t和stream_t的信息用以标注
create table datastream_label_raw_t 
select
	feed_t.id as feed_id,
	datastream_t.streamid as stream_id, 
	feed_t.description as description,
	feed_t.device_name as device_name, 
	feed_t.tags as feed_tag, 
	feed_t.title as feed_title,
	feed_t.lat as lat,
	feed_t.lng as lng,
	datastream_t.tags as stream_tag,
	datastream_t.current_value as cur_value,
	datastream_t.max_value as max_value,
	datastream_t.min_value as min_value
from datastream_t, feed_t 
where datastream_t.feedid = feed_t.id
group by feed_t.id, datastream_t.streamid;
alter table datastream_label_raw_t add column label varchar(200);

-- 选择数据点个数大于20的传感器作为数据源
create table datastream_label_t 
select * from datastream_label_raw_t inner join (
	select * from (
		select feedid, datastreamid, count(*) as cnt 
		from datapoint_t
		group by feedid, datastreamid
	) as T where cnt > 20
) as stream_seed on
stream_seed.feedid = datastream_label_raw_t.feed_id 
and stream_seed.datastreamid = datastream_label_raw_t.stream_id;
create table datastream_label_not_zero_t select * from datastream_label_t where cur_value != '0';
ALTER TABLE datastream_label_not_zero_t DROP COLUMN feedid;
ALTER TABLE datastream_label_not_zero_t DROP COLUMN datastreamid;

-- 借助20161204版本的标注内容进行补充
update datastream_label_not_zero_t a
set label = (
	select label 
	from curiosity_20161204.datastream_label_not_zero_t b
	where a.feed_id = b.feed_id and a.stream_id = b.stream_id
);

/**
 * 在curiosity_20161204上生成用于翻译的数据表
 */
create index c_index on datapoint_t(feedid, datastreamid);
-- select concat(description, '. ', device_name, '. ', exposure, '. ', title, '. ') from feed_t;
create table translation_t(
	feedid bigint,
	iana varchar(20),
	translated text	
);
create table feature_t(
	feedid bigint,
	location_type varchar(50),
	created date 
);
create table features_t select * from(
	select translation_t.feedid, translation_t.translated, translation_t.iana, feature_t.location_type, feature_t.created
	from translation_t 
	inner join feature_t on translation_t.feedid = feature_t.feedid
) as T;

select id, title from feed_t where tags is not null;
select * from features_t where iana='en';
select count(*) from features_t where iana='en' and translated is not NULL;
