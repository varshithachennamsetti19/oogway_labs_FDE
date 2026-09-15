/**
 * Sandboxed Artifact Viewer Controller
 */

export class ArtifactViewer {
  constructor() {
    this.viewerElem = document.getElementById("artifact-viewer");
    this.iframeElem = document.getElementById("artifact-frame");
    this.codeElem = document.getElementById("code-preview");
    this.tabPreviewBtn = document.getElementById("tab-preview");
    this.tabCodeBtn = document.getElementById("tab-code");
    this.btnClose = document.getElementById("btn-close-viewer");

    this.currentArtifact = null;
    this.initEvents();
  }

  initEvents() {
    if (this.btnClose) {
      this.btnClose.addEventListener("click", () => this.close());
    }

    if (this.tabPreviewBtn) {
      this.tabPreviewBtn.addEventListener("click", () => this.switchTab("preview"));
    }

    if (this.tabCodeBtn) {
      this.tabCodeBtn.addEventListener("click", () => this.switchTab("code"));
    }

    // Esc key close listener
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && this.isOpen()) {
        this.close();
      }
    });
  }

  open(artifactPayload) {
    this.currentArtifact = artifactPayload;
    if (!artifactPayload) return;

    // Inject HTML content into iframe safely via srcdoc
    const safeHtml = artifactPayload.content;

    // Strict Sandbox Protection: sandbox="allow-scripts" without allow-same-origin
    this.iframeElem.setAttribute("sandbox", "allow-scripts");
    this.iframeElem.srcdoc = safeHtml;

    // Set Raw Code view
    this.codeElem.textContent = safeHtml;

    this.switchTab("preview");
    this.viewerElem.classList.add("open");
  }

  close() {
    this.viewerElem.classList.remove("open");
    this.iframeElem.srcdoc = "";
  }

  isOpen() {
    return this.viewerElem.classList.contains("open");
  }

  switchTab(tabName) {
    if (tabName === "preview") {
      this.tabPreviewBtn.classList.add("active");
      this.tabCodeBtn.classList.remove("active");
      this.iframeElem.style.display = "block";
      this.codeElem.style.display = "none";
    } else {
      this.tabCodeBtn.classList.add("active");
      this.tabPreviewBtn.classList.remove("active");
      this.iframeElem.style.display = "none";
      this.codeElem.style.display = "block";
    }
  }
}
