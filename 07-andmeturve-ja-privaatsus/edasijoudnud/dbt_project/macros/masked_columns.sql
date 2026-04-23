-- Loob rollipohise SELECT-loendi vastavalt mudelil defineeritud meta-taggidele.
-- Kasutamine: {{ masked_columns('dim_users', role='marketing') }}
--
-- Meta-taggid schema.yml-is:
--   meta.allowed_roles: [analyst, marketing, ...]  -> tühi list = kõik rollid
--   meta.mask: mask_email / mask_varchar / mask_date / mask_int / mask_null / none
--
-- Tulemus: komadega eraldatud veergude loend, kus PII on maskeeritud

{% macro masked_columns(model_name, role) %}
  {%- set ns = namespace(selected=[]) -%}

  {%- for node_id, node in graph.nodes.items() -%}
    {%- if node.name == model_name and node.resource_type == 'model' -%}
      {%- for col_name, col in node.columns.items() -%}

        {%- set allowed = col.meta.get('allowed_roles', []) -%}
        {%- set mask = col.meta.get('mask', none) -%}

        {%- if not allowed or role in allowed -%}
          {%- if mask is none -%}
            {%- set ns.selected = ns.selected + [col_name] -%}
          {%- else -%}
            {%- set expr = apply_mask(mask, col_name) -%}
            {%- set ns.selected = ns.selected + [expr ~ ' AS ' ~ col_name] -%}
          {%- endif -%}
        {%- endif -%}

      {%- endfor -%}
    {%- endif -%}
  {%- endfor -%}

  {{ ns.selected | join(',\n    ') }}
{%- endmacro %}


-- Abimakro: kuvab maskeerimisfunktsiooni nime järgi
{% macro apply_mask(mask_type, col_name) -%}
  {%- if mask_type == 'mask_email' -%}
    {{ mask_email(col_name) }}
  {%- elif mask_type == 'mask_varchar' -%}
    {{ mask_varchar(col_name) }}
  {%- elif mask_type == 'mask_date' -%}
    {{ mask_date(col_name) }}
  {%- elif mask_type == 'mask_int' -%}
    {{ mask_int(col_name) }}
  {%- elif mask_type == 'mask_null' -%}
    {{ mask_null(col_name) }}
  {%- else -%}
    {{ col_name }}
  {%- endif -%}
{%- endmacro %}
