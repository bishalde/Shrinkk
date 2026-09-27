from flask import Blueprint, jsonify, session

analytics_bp = Blueprint("analytics", __name__)


def init_analytics_routes(analytics_model, link_model):

    @analytics_bp.route("/api/analytics/<link_id>", methods=["GET"])
    def get_analytics(link_id):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401

        link = link_model.find_by_id(link_id)
        if not link or str(link["user_id"]) != session["user_id"]:
            return jsonify({"error": "Link not found"}), 404

        stats = analytics_model.get_stats(link_id)
        return jsonify(stats)

    return analytics_bp
