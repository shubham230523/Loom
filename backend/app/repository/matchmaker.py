from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from backend.app.database import Opportunity, Repository
from backend.app.utils.logging import logger

class MatchmakerService:
    async def get_recommendations(
        self,
        db: AsyncSession,
        types: Optional[List[str]] = None,
        difficulties: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Finds the best matching opportunities based on user preferences.
        """
        query = select(Opportunity, Repository).join(Repository)

        filters = []
        if types:
            filters.append(Opportunity.type.in_(types))
        if difficulties:
            filters.append(Opportunity.difficulty.in_(difficulties))
        if languages:
            filters.append(Repository.language.in_(languages))

        if filters:
            query = query.where(and_(*filters))

        # Prioritize high score and high confidence
        query = query.order_by(Opportunity.score.desc(), Opportunity.confidence.desc())
        query = query.limit(limit)

        result = await db.execute(query)
        recommendations = []

        for opp, repo in result:
            recommendations.append({
                "opportunity": {
                    "id": str(opp.id),
                    "title": opp.title,
                    "description": opp.description,
                    "type": opp.type,
                    "difficulty": opp.difficulty,
                    "impact": opp.impact,
                    "score": opp.score,
                    "confidence": opp.confidence
                },
                "repository": {
                    "id": str(repo.id),
                    "full_name": repo.full_name,
                    "language": repo.language,
                    "owner": repo.owner,
                    "name": repo.name,
                    "stargazers_count": repo.stargazers_count
                }
            })

        return recommendations

matchmaker_service = MatchmakerService()
