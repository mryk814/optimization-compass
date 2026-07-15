PRAGMA foreign_keys = ON;

ALTER TABLE view_presets ADD COLUMN view_id TEXT NOT NULL
  CHECK (trim(view_id) <> '');
ALTER TABLE view_presets ADD COLUMN filter_policy_json TEXT NOT NULL
  CHECK (
    json_valid(filter_policy_json)
    AND json_type(filter_policy_json) = 'object'
    AND json_array_length(filter_policy_json, '$.groups') > 0
  );
ALTER TABLE view_presets ADD COLUMN limitations_ja TEXT NOT NULL
  CHECK (trim(limitations_ja) <> '');
ALTER TABLE view_presets ADD COLUMN limitations_en TEXT NOT NULL
  CHECK (trim(limitations_en) <> '');
ALTER TABLE view_presets ADD COLUMN focus_fallback_entity_types_json TEXT NOT NULL
  CHECK (
    json_valid(focus_fallback_entity_types_json)
    AND json_type(focus_fallback_entity_types_json) = 'array'
    AND json_array_length(focus_fallback_entity_types_json) > 0
  );

CREATE UNIQUE INDEX view_presets_view_id_unique ON view_presets(view_id);
