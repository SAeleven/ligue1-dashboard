{#
    Utilise le schéma défini dans dbt_project.yml (staging, intermediate, marts)
    tel quel, au lieu du comportement par défaut de dbt qui le préfixe
    par le schéma cible (main_staging…).
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
