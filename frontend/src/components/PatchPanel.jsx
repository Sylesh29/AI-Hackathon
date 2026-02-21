export default function PatchPanel({ patch, loading, onCopy, disabled }) {
  return (
    <article className="card">
      <div className="cardHeader">
        <h2>Patch</h2>
        <button type="button" className="button buttonSecondary" onClick={onCopy} disabled={disabled} aria-label="Copy patch snippet">
          Copy Patch
        </button>
      </div>

      <pre className="codeBlock">{patch || (loading ? "Generating patch..." : "Patch snippet will appear after run.")}</pre>
    </article>
  );
}
