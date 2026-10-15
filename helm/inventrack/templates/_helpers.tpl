{{/* Base name for every object: the release name, plus the chart name if it isn't already in it */}}
{{- define "it.fullname" -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}{{ .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else -}}{{ printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}{{- end -}}
{{- end -}}

{{- define "it.api" -}}{{ include "it.fullname" . }}-api{{- end -}}
{{- define "it.web" -}}{{ include "it.fullname" . }}-web{{- end -}}
{{- define "it.db" -}}{{ include "it.fullname" . }}-db{{- end -}}

{{- define "it.dbSecret" -}}
{{- default (printf "%s-db" (include "it.fullname" .)) .Values.database.existingSecret -}}
{{- end -}}

{{/* Labels on every object */}}
{{- define "it.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
app.kubernetes.io/part-of: inventrack
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end -}}

{{/* Stable selector labels. Usage: include "it.selector" (list . "api") */}}
{{- define "it.selector" -}}
app.kubernetes.io/name: {{ include "it.fullname" (index . 0) }}
app.kubernetes.io/instance: {{ (index . 0).Release.Name }}
app.kubernetes.io/component: {{ index . 1 }}
{{- end -}}

{{- define "it.image" -}}
{{- $img := index . 0 -}}{{- $ctx := index . 1 -}}
{{ $img.repository }}:{{ $img.tag | default $ctx.Chart.AppVersion }}
{{- end -}}

{{/* DB connection env, shared by the API and the migration Job */}}
{{- define "it.dbEnv" -}}
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "it.dbSecret" . }}
      key: {{ .Values.database.secretKey }}
- name: DATABASE_URL
  value: postgresql+psycopg://{{ .Values.database.user }}:$(DB_PASSWORD)@{{ include "it.db" . }}:5432/{{ .Values.database.name }}
{{- end -}}

{{/* Hardened container settings */}}
{{- define "it.securityContext" -}}
runAsNonRoot: true
allowPrivilegeEscalation: false
readOnlyRootFilesystem: {{ . }}
capabilities:
  drop: ["ALL"]
seccompProfile:
  type: RuntimeDefault
{{- end -}}
