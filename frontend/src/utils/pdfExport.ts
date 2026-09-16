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
  // Ensure element is visible and has dimensions
  if (!element || element.offsetWidth === 0 || element.offsetHeight === 0) {
    throw new Error('Element not visible or has no dimensions')
  }

  const canvas = await html2canvas(element, {
    scale: 1.5,
    useCORS: true,
    backgroundColor: '#ffffff',
    logging: false,
    allowTaint: true,  // Changed from false to allow cross-origin images
    windowWidth: 794,  // Fixed A4 width in pixels
    windowHeight: element.scrollHeight || 1123,
    onclone: (clonedDoc) => {
      // Remove stylesheets to avoid DaisyUI conflicts
      const styleTags = clonedDoc.querySelectorAll('style, link[rel="stylesheet"]')
      styleTags.forEach((el) => el.remove())
    },
  })

  if (!canvas || canvas.width === 0 || canvas.height === 0) {
    throw new Error('Canvas capture failed')
  }

  const imgW = canvas.width
  const imgH = canvas.height

  // Calculate how many mm tall the image is at A4 width
  const pdfImgH_MM = (imgH * A4_W_MM) / imgW

  const pdf = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  })

  let remainingH = pdfImgH_MM
  let positionInImg = 0
  let page = 0

  while (remainingH > 2) {
    if (page > 0) pdf.addPage()

    const sliceH = Math.min(remainingH, A4_H_MM)
    const srcY = (positionInImg * imgW) / A4_W_MM

    const sliceCanvas = document.createElement('canvas')
    const slicePixelH = (sliceH * imgW) / A4_W_MM
    sliceCanvas.width = imgW
    sliceCanvas.height = Math.ceil(slicePixelH)

    const ctx = sliceCanvas.getContext('2d')!
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, sliceCanvas.width, sliceCanvas.height)
    ctx.drawImage(canvas, 0, srcY, imgW, slicePixelH, 0, 0, imgW, slicePixelH)

    const sliceData = sliceCanvas.toDataURL('image/jpeg', 0.7)
    pdf.addImage(sliceData, 'JPEG', 0, 0, A4_W_MM, sliceH, undefined, 'FAST')

    remainingH -= sliceH
    positionInImg += sliceH
    page++
  }

  // Trigger download
  const blob = pdf.output('blob')
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
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
