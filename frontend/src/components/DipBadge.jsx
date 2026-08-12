export default function DipBadge({ level }) {
  return <span className={`badge badge-${level?.toLowerCase()}`}>{level}</span>;
}
