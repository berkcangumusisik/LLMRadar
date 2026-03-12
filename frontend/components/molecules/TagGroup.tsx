import { KeyMetricChip, ModelBadge, TagBadge } from "@/components/atoms";

interface TagGroupProps {
  categoryTags: string[];
  modelTags: string[];
  keyMetric: string | null;
}

export function TagGroup({ categoryTags, modelTags, keyMetric }: TagGroupProps) {
  if (!categoryTags.length && !modelTags.length && !keyMetric) return null;

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {categoryTags.map((tag) => (
        <TagBadge key={tag} tag={tag} />
      ))}
      {modelTags.map((model) => (
        <ModelBadge key={model} model={model} />
      ))}
      {keyMetric && <KeyMetricChip metric={keyMetric} />}
    </div>
  );
}
