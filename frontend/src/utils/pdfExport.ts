/**
 * pdfExport — renders a DOM element to a PDF using html2canvas + jspdf.
 * Supports multi-page output when content exceeds A4 height.
 */

import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'

/** A4 dimensions in mm. */
const A4_W_MM = 210
const A4_H_MM = 297

/**
 * Generates and downloads a PDF from a given DOM element.
 * @param element  The element to capture (should be A4-width in pixels).
 * @param filename Download filename (e.g. "RiskTrail_Informe_2026-09-08.pdf").
 */
export async function exportElementAsPdf(element: HTMLElement, filename: string): Promise<void> {
  const canvas = await html2canvas(element, {
    scale: 2,
    useCORS: true,
    backgroundColor: '#ffffff',
    logging: false,
    allowTaint: false,
    windowWidth: element.scrollWidth,
    windowHeight: element.scrollHeight,
    onclone: (clonedDoc) => {
      // Strip all global stylesheets/styles in the cloned document so html2canvas
      // never encounters DaisyUI's oklch() color functions. The template uses
      // 100% inline hex/rgb styles, so removing stylesheets is completely safe.
      const styleTags = clonedDoc.querySelectorAll('style, link[rel="stylesheet"]')
      styleTags.forEach((el) => el.remove())
    },
  })

  const imgData = canvas.toDataURL('image/png')
  const imgW = canvas.width
  const imgH = canvas.height

  // Calculate how many mm tall the image is at A4 width.
  const pdfImgH_MM = (imgH * A4_W_MM) / imgW

  const pdf = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  })

  let remainingH = pdfImgH_MM
  let positionInImg = 0
  let page = 0

  // Only paginate if remaining height exceeds 2mm (prevents rounding-induced blank pages)
  while (remainingH > 2) {
    if (page > 0) pdf.addPage()

    // How many mm of the image fit on this page (minus top margin on first page)
    const sliceH = Math.min(remainingH, A4_H_MM)

    // The source y offset in image pixels
    const srcY = (positionInImg * imgW) / A4_W_MM

    // Create a sub-canvas for this slice to avoid distortion
    const sliceCanvas = document.createElement('canvas')
    const slicePixelH = (sliceH * imgW) / A4_W_MM
    sliceCanvas.width = imgW
    sliceCanvas.height = Math.ceil(slicePixelH)

    const ctx = sliceCanvas.getContext('2d')!
    ctx.drawImage(canvas, 0, srcY, imgW, slicePixelH, 0, 0, imgW, slicePixelH)

    const sliceData = sliceCanvas.toDataURL('image/png')
    pdf.addImage(sliceData, 'PNG', 0, 0, A4_W_MM, sliceH)

    remainingH -= sliceH
    positionInImg += sliceH
    page++
  }

  pdf.save(filename)
}

/**
 * Builds a standardised filename for the route report.
 */
export function buildReportFilename(routeName: string | null, routeId: string): string {
  const name = routeName
    ? routeName.replace(/[^a-zA-Z0-9_\-\u00C0-\u024F]/g, '_').slice(0, 40)
    : routeId.slice(0, 8)
  const date = new Date().toISOString().slice(0, 10)
  return `RiskTrail_Informe_${name}_${date}.pdf`
}
