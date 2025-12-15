function toggleCollection(postId, btn) {
  fetch("/toggle-collection", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ post_id: postId })
  })
  .then(res => res.json())
  .then(data => {
    btn.innerText = data.status === "added"
      ? "取消收藏"
      : "收藏";
  });
}
