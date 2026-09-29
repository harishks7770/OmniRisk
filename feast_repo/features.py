from datetime import timedelta
from feast import Entity, Field, FeatureView, FileSource, ValueType
from feast.types import Float64, Int64, String

user_entity = Entity(
    name="user_id",
    value_type=ValueType.STRING,
    join_keys=["user_id"],
    description="User identifier"
)

# Explicitly target the single compacted snapshot file
user_features_source = FileSource(
    name="user_features_source",
    path="../data/user_features_snapshot.parquet",
    timestamp_field="event_timestamp"
)

user_features_view = FeatureView(
    name="user_features",
    entities=[user_entity],
    ttl=timedelta(days=7),
    schema=[
        Field(name="transaction_count_1h", dtype=Int64),
        Field(name="total_spend_1h", dtype=Float64)
    ],
    online=True,
    source=user_features_source,
)